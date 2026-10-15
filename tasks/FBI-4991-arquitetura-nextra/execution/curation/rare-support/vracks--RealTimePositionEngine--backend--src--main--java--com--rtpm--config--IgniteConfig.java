package com.rtpm.config;

import com.rtpm.domain.Position;
import com.rtpm.domain.PositionKey;
import com.rtpm.domain.Price;
import com.rtpm.exception.domain.ExceptionKey;
import com.rtpm.exception.domain.TradeException;
import com.rtpm.recon.domain.MatchKey;
import com.rtpm.recon.domain.MatchRuleSet;
import com.rtpm.recon.domain.ReconGroup;
import org.apache.ignite.Ignite;
import org.apache.ignite.Ignition;
import org.apache.ignite.cache.CacheAtomicityMode;
import org.apache.ignite.cache.CacheMode;
import org.apache.ignite.cache.CacheRebalanceMode;
import org.apache.ignite.cache.CacheWriteSynchronizationMode;
import org.apache.ignite.configuration.CacheConfiguration;
import org.apache.ignite.configuration.IgniteConfiguration;
import org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi;
import org.apache.ignite.spi.discovery.tcp.ipfinder.vm.TcpDiscoveryVmIpFinder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.cache.configuration.FactoryBuilder;
import javax.cache.expiry.CreatedExpiryPolicy;
import javax.cache.expiry.Duration;
import javax.cache.expiry.TouchedExpiryPolicy;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Starts the Ignite <em>client</em> node and declares the cache topology.
 *
 * <p>Configuration is programmatic rather than XML on purpose. The obvious alternative,
 * Ignite's {@code ignite-spring} module, transitively depends on Spring Framework 5, which
 * cannot coexist with Spring Boot 3's Spring 6 and {@code jakarta.*} namespace. Building an
 * {@link IgniteConfiguration} by hand needs only {@code ignite-core} — verified to have no
 * Spring dependency at all — and has the side benefit of putting the cache topology in
 * type-checked code where it can be read alongside the domain model.
 */
@Configuration
public class IgniteConfig {

    private static final Logger log = LoggerFactory.getLogger(IgniteConfig.class);

    /** Positions survive one node loss; a second backup would cost writes for little gain here. */
    private static final int POSITION_BACKUPS = 1;

    /** Trade ids only need to outlive plausible Kafka redelivery, not the whole session. */
    private static final Duration PROCESSED_TRADE_TTL = new Duration(TimeUnit.HOURS, 2);

    /**
     * How long a reconciliation group is retained after its last update.
     *
     * <p>Bounded from below by the missing-window: a group evicted before a late record
     * arrives can never be reclassified, turning temporary feed lag into a permanent false
     * Missing. Five minutes is ten times the 30-second window, which is ample.
     *
     * <p>Bounded from above by group size. Because the match key has no time component,
     * retention directly determines how many records accumulate under one key — and the
     * matcher scores a cross product within each group, so retention has a <em>quadratic</em>
     * effect on matching cost. Thirty minutes was the original value and produced groups of
     * 59 × 55 within minutes of starting the feed.
     */
    private static final Duration RECON_GROUP_TTL = new Duration(TimeUnit.MINUTES, 5);

    /**
     * Lookback for the duplicate-trade rule, expressed as cache expiry.
     *
     * <p>Making the window a TTL rather than a stored timestamp means memory is bounded by
     * the window rather than by total trade volume — a comparison-based approach would retain
     * every fingerprint forever to answer a question about the last two minutes.
     */
    private static final Duration DUPLICATE_WINDOW = new Duration(TimeUnit.MINUTES, 2);

    @Value("${rtpm.ignite.addresses:127.0.0.1:47500..47509}")
    private String igniteAddresses;

    /**
     * Explicit Ignite work directory.
     *
     * <p>Left blank outside containers so Ignite uses its own default, which is what the
     * tests rely on. In the container it is set to a path owned by the unprivileged runtime
     * user, because Ignite's default of {@code $CWD/ignite/work} is not writable there.
     */
    @Value("${rtpm.ignite.work-dir:}")
    private String igniteWorkDir;

    @Bean(destroyMethod = "close")
    public Ignite ignite() {
        IgniteConfiguration cfg = new IgniteConfiguration();

        cfg.setIgniteInstanceName("rtpm-client");

        if (!igniteWorkDir.isBlank()) {
            cfg.setWorkDirectory(igniteWorkDir);
        }

        // A client node holds no data and owns no partitions. It participates in the
        // cluster so it can run continuous queries and route EntryProcessors, while the
        // two server containers do the actual storage and computation.
        cfg.setClientMode(true);

        // Lets this node ship PositionUpdateProcessor to whichever server owns the key
        // without an application JAR being present on the servers.
        cfg.setPeerClassLoadingEnabled(true);

        cfg.setFailureDetectionTimeout(10_000L);
        cfg.setClientFailureDetectionTimeout(30_000L);

        List<String> addresses = Arrays.stream(igniteAddresses.split(","))
                .map(String::trim)
                .filter(address -> !address.isEmpty())
                .toList();
        log.info("Ignite client discovery addresses: {}", addresses);

        TcpDiscoveryVmIpFinder ipFinder = new TcpDiscoveryVmIpFinder();
        ipFinder.setAddresses(addresses);

        TcpDiscoverySpi discoverySpi = new TcpDiscoverySpi();
        discoverySpi.setIpFinder(ipFinder);
        cfg.setDiscoverySpi(discoverySpi);

        cfg.setCacheConfiguration(
                positionCache(), priceCache(), processedTradeCache(),
                reconGroupCache(), reconRuleCache(), reconSeenRecordCache(),
                referenceCache(CacheNames.SECURITIES), referenceCache(CacheNames.COUNTERPARTIES),
                referenceCache(CacheNames.ACCOUNTS), referenceCache(CacheNames.EXCEPTION_RULES),
                tradeExceptionCache(), exceptionSeenRecordCache(), tradeFingerprintCache());

        Ignite ignite = Ignition.start(cfg);
        log.info("Ignite client started. Cluster has {} server node(s).",
                ignite.cluster().forServers().nodes().size());
        return ignite;
    }

    /**
     * Positions: partitioned and colocated by account via {@code PositionKey}'s
     * {@code @AffinityKeyMapped} field.
     *
     * <p>ATOMIC rather than TRANSACTIONAL because each trade mutates exactly one key, and
     * that mutation is made atomic by running it inside an {@code EntryProcessor} on the
     * owning node. Transactions would add two-phase-commit overhead to buy a guarantee the
     * access pattern does not need.
     */
    private CacheConfiguration<PositionKey, Position> positionCache() {
        CacheConfiguration<PositionKey, Position> cfg = new CacheConfiguration<>(CacheNames.POSITIONS);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        // Wait for backups before acknowledging: a position that survives the write call
        // but not a node failure would be silently wrong, and positions are cumulative so
        // the error would never self-correct.
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setRebalanceMode(CacheRebalanceMode.SYNC);
        cfg.setStatisticsEnabled(true);
        return cfg;
    }

    /**
     * Prices: replicated, so every valuation reads locally.
     *
     * <p>The inverse trade-off to positions. Prices are few and read constantly, so paying
     * to copy every write to every node removes a network hop from the hottest read path.
     */
    private CacheConfiguration<String, Price> priceCache() {
        CacheConfiguration<String, Price> cfg = new CacheConfiguration<>(CacheNames.PRICES);
        cfg.setCacheMode(CacheMode.REPLICATED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        // Prices are regenerated by the next tick, so a lost write is self-healing.
        // Unlike positions, this cache can afford the faster acknowledgement.
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.PRIMARY_SYNC);
        cfg.setStatisticsEnabled(true);
        return cfg;
    }

    /**
     * Seen trade ids, used to make at-least-once Kafka delivery safe.
     *
     * <p>Entries expire on a TTL because this is a duplicate guard, not an audit log —
     * without expiry it would grow without bound for the life of the cluster.
     */
    /**
     * Reconciliation groups: partitioned and colocated by account, matching the position
     * cache so an account's recon state and its positions live on the same node.
     *
     * <p>Unlike positions, this cache <strong>expires</strong>. Reconciliation accumulates a
     * new key per account/security/date rather than folding into fixed state, and every
     * unpaired record that never finds a counterpart would otherwise be retained forever.
     * The TTL is set well above the missing-window so a late arrival can still reclassify a
     * group before it is evicted — expiring faster than the window would silently destroy
     * the very records the window exists to wait for.
     *
     * <p>Expiry is on <em>update</em>, not creation: a group that is still receiving records
     * is still live, and should not vanish mid-conversation.
     */
    private CacheConfiguration<MatchKey, ReconGroup> reconGroupCache() {
        CacheConfiguration<MatchKey, ReconGroup> cfg = new CacheConfiguration<>(CacheNames.RECON_GROUPS);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setRebalanceMode(CacheRebalanceMode.SYNC);
        cfg.setExpiryPolicyFactory(FactoryBuilder.factoryOf(
                new TouchedExpiryPolicy(RECON_GROUP_TTL)));
        cfg.setStatisticsEnabled(true);
        return cfg;
    }

    /**
     * The active matching rule set, under a single key.
     *
     * <p>REPLICATED for the same reason as prices: it is minuscule and read on every group
     * evaluation, so copying it to every node removes a network hop from the hottest read
     * path in the reconciliation engine.
     */
    private CacheConfiguration<String, MatchRuleSet> reconRuleCache() {
        CacheConfiguration<String, MatchRuleSet> cfg = new CacheConfiguration<>(CacheNames.RECON_RULES);
        cfg.setCacheMode(CacheMode.REPLICATED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        return cfg;
    }

    /** Feed-level duplicate guard, mirroring {@link #processedTradeCache()}. */
    private CacheConfiguration<String, Boolean> reconSeenRecordCache() {
        CacheConfiguration<String, Boolean> cfg = new CacheConfiguration<>(CacheNames.RECON_SEEN_RECORDS);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setExpiryPolicyFactory(FactoryBuilder.factoryOf(
                new CreatedExpiryPolicy(PROCESSED_TRADE_TTL)));
        return cfg;
    }

    /**
     * Reference data and exception rules — replicated, keyed by a natural id.
     *
     * <p>All four are read on <strong>every</strong> rule evaluation, so at 1000 trades/sec
     * against a dozen rules a partitioned lookup would put a network hop on the hottest path
     * in the engine. They are also tiny and rarely written, which is exactly the shape
     * replication is for — the same reasoning as the {@code prices} cache.
     *
     * <p>No expiry: this is authoritative reference data, not a derived cache. An entry
     * quietly expiring would make a known security look unknown and raise a storm of
     * fabricated exceptions.
     */
    private <V> CacheConfiguration<String, V> referenceCache(String name) {
        CacheConfiguration<String, V> cfg = new CacheConfiguration<>(name);
        cfg.setCacheMode(CacheMode.REPLICATED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        return cfg;
    }

    /**
     * Raised exceptions: partitioned and colocated by account.
     *
     * <p><strong>No TTL.</strong> Unlike reconciliation groups, these are entities carrying an
     * owner, an acknowledgement and an SLA record — state no rule can regenerate. Expiring one
     * would silently discard an analyst's work and quietly improve the SLA statistics by
     * deleting the evidence. Resolved exceptions are archived explicitly rather than evicted.
     */
    private CacheConfiguration<ExceptionKey, TradeException> tradeExceptionCache() {
        CacheConfiguration<ExceptionKey, TradeException> cfg =
                new CacheConfiguration<>(CacheNames.TRADE_EXCEPTIONS);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setRebalanceMode(CacheRebalanceMode.SYNC);
        cfg.setStatisticsEnabled(true);
        return cfg;
    }

    /** The exception engine consumes independently of recon, so it needs its own guard. */
    private CacheConfiguration<String, Boolean> exceptionSeenRecordCache() {
        CacheConfiguration<String, Boolean> cfg =
                new CacheConfiguration<>(CacheNames.EXCEPTION_SEEN_RECORDS);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setExpiryPolicyFactory(FactoryBuilder.factoryOf(
                new CreatedExpiryPolicy(PROCESSED_TRADE_TTL)));
        return cfg;
    }

    /**
     * Trade fingerprints backing the duplicate-detection rule.
     *
     * <p>The TTL <em>is</em> the detection window: a fingerprint that has expired is no longer
     * a duplicate. Expressing the window as cache expiry rather than as a timestamp comparison
     * means the memory footprint is bounded by the window rather than by total volume.
     */
    private CacheConfiguration<String, Long> tradeFingerprintCache() {
        CacheConfiguration<String, Long> cfg = new CacheConfiguration<>(CacheNames.TRADE_FINGERPRINTS);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setExpiryPolicyFactory(FactoryBuilder.factoryOf(
                new CreatedExpiryPolicy(DUPLICATE_WINDOW)));
        return cfg;
    }

    private CacheConfiguration<String, Boolean> processedTradeCache() {
        CacheConfiguration<String, Boolean> cfg = new CacheConfiguration<>(CacheNames.PROCESSED_TRADES);
        cfg.setCacheMode(CacheMode.PARTITIONED);
        cfg.setAtomicityMode(CacheAtomicityMode.ATOMIC);
        cfg.setBackups(POSITION_BACKUPS);
        cfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
        cfg.setExpiryPolicyFactory(FactoryBuilder.factoryOf(
                new CreatedExpiryPolicy(PROCESSED_TRADE_TTL)));
        return cfg;
    }
}
