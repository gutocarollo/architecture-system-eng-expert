# S6 — reparo das referências específicas de R1

Este registro conserva a captura de fontes primárias usada para acrescentar um par de base e aplicação OSS em cada uma das 59 entradas dos grupos 11–14 e corrigir somente as linhas prioritárias 23/24. Os recursos de produção não foram consultados novamente. O recorte de escrita não inclui explicações, índices, matriz ou packet. O council independente continua responsável pelo aceite.

O checkout era `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. A página prioritária antes do reparo tinha SHA-256 `e6b2b662b0cf0c9ee4ef7628bd1d8b79e405ab3d37b342a6aede1a792524a8cd`. A curadoria L6B lida tinha SHA-256 `550e2153fb7099e6686ba1d46d49080ff0df8f07ef7c7356f71a1f98c038d4dc`.

Context7 `/vercel/next.js` retornou o contrato oficial de adoção incremental: o resolver verifica páginas novas antes de usar fallback para o site existente. A configuração oficial, o resolver e o proxy do produto são capturados separadamente abaixo.

## Captura primária de 2026-10-14 19:47 UTC


### Fonte `next-rewrites`

```json
{
  "id": "next-rewrites",
  "repo": "vercel/next.js",
  "requested_ref": "canary",
  "revision": "58f4af6ab2d9142acb3d20e1b070359f608f7b35",
  "path": "docs/01-app/03-api-reference/05-config/01-next-config-js/rewrites.mdx",
  "url": "https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/docs/01-app/03-api-reference/05-config/01-next-config-js/rewrites.mdx",
  "observedUTC": "2026-10-14T19:47:49.648986+00:00",
  "HTTPstatus": 200,
  "sha256": "68446fc1d09fe7c2d258a1bfcfe678bde797043f6be2e1d92fd1a2fb75f19000",
  "line_count": 479,
  "matches": [
    {
      "line": 72,
      "text": "      fallback: ["
    },
    {
      "line": 98,
      "text": "8. `fallback` rewrites are checked/applied, these are applied before rendering the 404 page and after dynamic routes/all static assets have been checked. If you use [fallback: true/'blocking'](/docs/p"
    },
    {
      "line": 110,
      "text": "7. `fallback` rewrites are checked/applied, these are applied before rendering the 404 page and after dynamic routes/all static assets have been checked. If you use [fallback: true/'blocking'](/docs/p"
    },
    {
      "line": 376,
      "text": "### Incremental adoption of Next.js"
    },
    {
      "line": 386,
      "text": "      fallback: ["
    },
    {
      "line": 389,
      "text": "          destination: `https://custom-routes-proxying-endpoint.vercel.app/:path*`,"
    }
  ]
}
```

### Fonte `next-resolver`

```json
{
  "id": "next-resolver",
  "repo": "vercel/next.js",
  "requested_ref": "canary",
  "revision": "58f4af6ab2d9142acb3d20e1b070359f608f7b35",
  "path": "packages/next/src/server/lib/router-utils/resolve-routes.ts",
  "url": "https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/packages/next/src/server/lib/router-utils/resolve-routes.ts",
  "observedUTC": "2026-10-14T19:47:49.649270+00:00",
  "HTTPstatus": 200,
  "sha256": "5421c2fc39bd1a1d8909cffdd658230f892a4f96037958bf013f56ac22a2296b",
  "line_count": 972,
  "matches": [
    {
      "line": 103,
      "text": "      { match: () => ({}), name: 'check_fs' },"
    },
    {
      "line": 115,
      "text": "      ...(opts.minimalMode ? [] : fsChecker.rewrites.fallback),"
    },
    {
      "line": 498,
      "text": "        if (route.name === 'check_fs') {"
    },
    {
      "line": 815,
      "text": "          route.destination"
    },
    {
      "line": 819,
      "text": "            destination: route.destination,"
    },
    {
      "line": 864,
      "text": "        if (route.destination) {"
    },
    {
      "line": 869,
      "text": "            destination: route.destination,"
    },
    {
      "line": 893,
      "text": "            // the final route destination."
    },
    {
      "line": 935,
      "text": "        if (route.check) {"
    }
  ]
}
```

### Fonte `next-proxy`

```json
{
  "id": "next-proxy",
  "repo": "vercel/next.js",
  "requested_ref": "canary",
  "revision": "58f4af6ab2d9142acb3d20e1b070359f608f7b35",
  "path": "packages/next/src/server/lib/router-utils/proxy-request.ts",
  "url": "https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/packages/next/src/server/lib/router-utils/proxy-request.ts",
  "observedUTC": "2026-10-14T19:47:49.649338+00:00",
  "HTTPstatus": 200,
  "sha256": "fb019fe6202032daf47e1c9604f88da77fbd4c9833dfa1b4546b980a148fa465",
  "line_count": 141,
  "matches": [
    {
      "line": 10,
      "text": "export async function proxyRequest("
    },
    {
      "line": 24,
      "text": "  // We just make sure this is a valid URL since httpxy would only parse it"
    },
    {
      "line": 27,
      "text": "  const { ProxyServer } ="
    },
    {
      "line": 28,
      "text": "    require('next/dist/compiled/httpxy') as typeof import('next/dist/compiled/httpxy')"
    },
    {
      "line": 30,
      "text": "  const proxy = new ProxyServer({"
    },
    {
      "line": 31,
      "text": "    target,"
    },
    {
      "line": 45,
      "text": "  // httpxy does not properly detect a client disconnect in newer"
    }
  ]
}
```

### Fonte `gl-multistore`

```json
{
  "id": "gl-multistore",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "lib/gitlab/redis/multi_store.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb",
  "observedUTC": "2026-10-14T19:47:49.649384+00:00",
  "HTTPstatus": 200,
  "sha256": "810ef1097d9ea059f5abf2eeb604fb0d210534da3a8b0b5f776fae9663b9ef28",
  "line_count": 519,
  "matches": [
    {
      "line": 8,
      "text": "      class PipelinedDiffError < StandardError"
    },
    {
      "line": 163,
      "text": "      # To transition between two Redis store, `primary_pool` should be the connection pool for the target store,"
    },
    {
      "line": 168,
      "text": "      # - Turning use_primary_and_secondary_stores_for_<instance_name> on: The store writes to both instances."
    },
    {
      "line": 171,
      "text": "      # - Turning use_primary_store_as_default_for_<instance_name> on: The behavior is the same as above,"
    },
    {
      "line": 173,
      "text": "      # - Turning use_primary_and_secondary_stores_for_<instance_name> off: commands are executed in the primary store."
    },
    {
      "line": 285,
      "text": "        # We interpolate the feature flag name within `Feature.enabled?` instead of defining a variable to allow"
    },
    {
      "line": 288,
      "text": "          Feature.enabled?( # rubocop:disable Cop/FeatureFlagUsage -- The flags are dynamic"
    },
    {
      "line": 296,
      "text": "        # We interpolate the feature flag name within `Feature.enabled?` instead of defining a variable to allow"
    },
    {
      "line": 299,
      "text": "          Feature.enabled?( # rubocop:disable Cop/FeatureFlagUsage -- The flags are dynamic"
    },
    {
      "line": 331,
      "text": "      def default_store"
    },
    {
      "line": 335,
      "text": "      def non_default_store"
    },
    {
      "line": 425,
      "text": "      def write_both(command_name, ...)"
    },
    {
      "line": 430,
      "text": "          send_command(non_default_store, command_name, ...)"
    },
    {
      "line": 440,
      "text": "      def pipelined_both(command_name, ...)"
    },
    {
      "line": 444,
      "text": "          result_non_default = send_command(non_default_store, command_name, ...)"
    },
    {
      "line": 450,
      "text": "        if result_non_default && result_non_default != result_default"
    },
    {
      "line": 451,
      "text": "          error = PipelinedDiffError.new(result_non_default, result_default)"
    }
  ]
}
```

### Fonte `gl-wrapper`

```json
{
  "id": "gl-wrapper",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "lib/gitlab/redis/wrapper.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/wrapper.rb",
  "observedUTC": "2026-10-14T19:47:49.649445+00:00",
  "HTTPstatus": 200,
  "sha256": "f14929c51892749fa83575d2307482b3884f204b553c9d976957f13ca08bbb31",
  "line_count": 289,
  "matches": [
    {
      "line": 47,
      "text": "                      ConnectionPool.new(size: pool_size, name: store_name.underscore) { redis }"
    },
    {
      "line": 112,
      "text": "        def init_redis(config)"
    },
    {
      "line": 114,
      "text": "            ::Redis::Cluster.new(config.merge({ concurrency: { model: :none } }))"
    },
    {
      "line": 116,
      "text": "            ::Redis.new(config)"
    }
  ]
}
```

### Fonte `gl-feature`

```json
{
  "id": "gl-feature",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "lib/feature.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/feature.rb",
  "observedUTC": "2026-10-14T19:47:49.649487+00:00",
  "HTTPstatus": 200,
  "sha256": "2708bb26af5fd26c6a0652027af7702167d0d4e6eedd7256d10320d38e3df313",
  "line_count": 722,
  "matches": [
    {
      "line": 24,
      "text": "    # Flipper::Adapters::ActiveRecord::Model, which inherits ActiveRecord::Base"
    },
    {
      "line": 89,
      "text": "  class ActiveSupportCacheStoreAdapter < Flipper::Adapters::ActiveSupportCacheStore"
    },
    {
      "line": 141,
      "text": "    def enabled?(key, thing = nil, type: nil, default_enabled_if_undefined: nil)"
    },
    {
      "line": 158,
      "text": "    def disabled?(key, thing = nil, type: nil, default_enabled_if_undefined: nil)"
    },
    {
      "line": 193,
      "text": "    def disable(key, thing = false)"
    },
    {
      "line": 259,
      "text": "    def disable_percentage_of_time(key)"
    },
    {
      "line": 264,
      "text": "    def enable_percentage_of_actors(key, percentage)"
    },
    {
      "line": 269,
      "text": "        flag.enable_percentage_of_actors(percentage)"
    },
    {
      "line": 273,
      "text": "    def disable_percentage_of_actors(key)"
    },
    {
      "line": 355,
      "text": "    # rubocop: disable CodeReuse/ActiveRecord -- rubocop doesn't recognize Flipper::Adapters::ActiveRecord::Gate as ActiveRecord."
    },
    {
      "line": 423,
      "text": "    # NOTE: it is not safe to call `Flipper::Feature#enabled?` outside the block"
    },
    {
      "line": 473,
      "text": "      active_record_adapter = Flipper::Adapters::ActiveRecord.new("
    },
    {
      "line": 483,
      "text": "        Flipper::Adapters::ActiveSupportCacheStore.new(redis_cache_adapter, l1_cache_backend, 1.minute)"
    },
    {
      "line": 543,
      "text": "      return if thing.is_a?(Flipper::Types::Group) || thing.respond_to?(:flipper_id)"
    }
  ]
}
```

### Fonte `gl-expand`

```json
{
  "id": "gl-expand",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "v18.10.0",
  "revision": "39f78019749fcb2458260e65c987c59ca7a37a2c",
  "path": "db/migrate/20260114180938_initialize_conversion_of_bulk_import_entities_source_xid_to_bigint.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/39f78019749fcb2458260e65c987c59ca7a37a2c/db/migrate/20260114180938_initialize_conversion_of_bulk_import_entities_source_xid_to_bigint.rb",
  "observedUTC": "2026-10-14T19:47:49.649538+00:00",
  "HTTPstatus": 200,
  "sha256": "b3034e542bdd353e0aa4e03828695d74f2d26db8bdf92bc07cc84dba82cc478e",
  "line_count": 17,
  "matches": [
    {
      "line": 7,
      "text": "  TABLE = :bulk_import_entities"
    },
    {
      "line": 8,
      "text": "  COLUMNS = %i[source_xid]"
    },
    {
      "line": 11,
      "text": "    initialize_conversion_of_integer_to_bigint(TABLE, COLUMNS)"
    },
    {
      "line": 15,
      "text": "    revert_initialize_conversion_of_integer_to_bigint(TABLE, COLUMNS)"
    }
  ]
}
```

### Fonte `gl-backfill`

```json
{
  "id": "gl-backfill",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "v18.10.0",
  "revision": "39f78019749fcb2458260e65c987c59ca7a37a2c",
  "path": "db/post_migrate/20260114180943_backfill_bulk_import_entities_source_xid_for_bigint_conversion.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/39f78019749fcb2458260e65c987c59ca7a37a2c/db/post_migrate/20260114180943_backfill_bulk_import_entities_source_xid_for_bigint_conversion.rb",
  "observedUTC": "2026-10-14T19:47:49.649579+00:00",
  "HTTPstatus": 200,
  "sha256": "c596585ca11fd287bf5dcf222cd644609379c12ce36084cf4eecee1659ac1350",
  "line_count": 17,
  "matches": [
    {
      "line": 7,
      "text": "  TABLE = :bulk_import_entities"
    },
    {
      "line": 8,
      "text": "  COLUMNS = %i[source_xid]"
    },
    {
      "line": 11,
      "text": "    backfill_conversion_of_integer_to_bigint(TABLE, COLUMNS, sub_batch_size: 200)"
    },
    {
      "line": 15,
      "text": "    revert_backfill_conversion_of_integer_to_bigint(TABLE, COLUMNS)"
    }
  ]
}
```

### Fonte `gl-finalize`

```json
{
  "id": "gl-finalize",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "db/post_migrate/20260429093419_finalize_bulk_import_entities_source_xid_bigint_conversion.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260429093419_finalize_bulk_import_entities_source_xid_bigint_conversion.rb",
  "observedUTC": "2026-10-14T19:47:49.972938+00:00",
  "HTTPstatus": 200,
  "sha256": "87c9d89f1714f8c4faf94efa293cd1437329df6d4efa66ed1793f3fe511f36fa",
  "line_count": 24,
  "matches": [
    {
      "line": 10,
      "text": "  TABLE_NAME = :bulk_import_entities"
    },
    {
      "line": 11,
      "text": "  COLUMN_NAME = :source_xid"
    },
    {
      "line": 14,
      "text": "    ensure_backfill_conversion_of_integer_to_bigint_is_finished("
    },
    {
      "line": 15,
      "text": "      TABLE_NAME,"
    },
    {
      "line": 16,
      "text": "      [COLUMN_NAME],"
    }
  ]
}
```

### Fonte `gl-swap`

```json
{
  "id": "gl-swap",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "db/post_migrate/20260429093420_swap_columns_for_bulk_import_entities_source_xid_bigint_conversion.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260429093420_swap_columns_for_bulk_import_entities_source_xid_bigint_conversion.rb",
  "observedUTC": "2026-10-14T19:47:49.985704+00:00",
  "HTTPstatus": 200,
  "sha256": "fbb160f25a4674a67d38cca775eb6ffab4beacc33f2c3f4e4064eca9eca72fbe",
  "line_count": 32,
  "matches": [
    {
      "line": 10,
      "text": "  TABLE_NAME = :bulk_import_entities"
    },
    {
      "line": 11,
      "text": "  COLUMN_NAME = :source_xid"
    },
    {
      "line": 26,
      "text": "      swap_columns(TABLE_NAME, COLUMN_NAME, convert_to_bigint_column(COLUMN_NAME))"
    },
    {
      "line": 28,
      "text": "      reset_all_trigger_functions(TABLE_NAME)"
    }
  ]
}
```

### Fonte `gl-cleanup`

```json
{
  "id": "gl-cleanup",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "db/post_migrate/20260518124649_clean_up_bigint_conversion_for_bulk_import_entities.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260518124649_clean_up_bigint_conversion_for_bulk_import_entities.rb",
  "observedUTC": "2026-10-14T19:47:49.994504+00:00",
  "HTTPstatus": 200,
  "sha256": "9b9aa733da1e7049a4b0d1f4cfbb20cd2c96d68ea81a00346ef5852e121eab70",
  "line_count": 16,
  "matches": [
    {
      "line": 6,
      "text": "  TABLE = :bulk_import_entities"
    },
    {
      "line": 7,
      "text": "  COLUMNS = %i[source_xid]"
    },
    {
      "line": 10,
      "text": "    cleanup_conversion_of_integer_to_bigint(TABLE, COLUMNS)"
    },
    {
      "line": 14,
      "text": "    restore_conversion_of_integer_to_bigint(TABLE, COLUMNS)"
    }
  ]
}
```

### Fonte `gl-multidb`

```json
{
  "id": "gl-multidb",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "doc/development/database/multiple_databases.md",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/doc/development/database/multiple_databases.md",
  "observedUTC": "2026-10-14T19:47:50.001505+00:00",
  "HTTPstatus": 200,
  "sha256": "bbc45c034488ad948285ee9f6a74be854ce8d1b33ecd7c20a78901ad0b4c05af",
  "line_count": 861,
  "matches": [
    {
      "line": 9,
      "text": "[decomposed the GitLab application database into multiple databases](https://gitlab.com/groups/gitlab-org/-/work_items/6168)."
    },
    {
      "line": 10,
      "text": "The main databases are `main`, `ci`, and `sec`. GitLab supports being run with one, two, or three databases."
    },
    {
      "line": 11,
      "text": "On GitLab.com we are using separate `main`, `ci`, and `sec` databases."
    },
    {
      "line": 31,
      "text": "| `gitlab_ci` | All CI tables that are being stored in the `ci:` database (for example, `ci_pipelines`, `ci_builds`) | |"
    },
    {
      "line": 32,
      "text": "| `gitlab_ci_cell_local` | See [Cells / Organizations schemas](../cells/_index.md#available-cells--organization-schemas) | |"
    },
    {
      "line": 46,
      "text": "- `ApplicationRecord` for `gitlab_main_org`"
    },
    {
      "line": 47,
      "text": "- `Ci::ApplicationRecord` for `gitlab_ci`"
    },
    {
      "line": 50,
      "text": "- `PackageMetadata::ApplicationRecord` for `gitlab_pm`"
    },
    {
      "line": 51,
      "text": "- `SecApplicationRecord` for `gitlab_sec`"
    },
    {
      "line": 138,
      "text": "Because GitLab can be run with multiple separate databases, referencing `main`"
    },
    {
      "line": 570,
      "text": "ApplicationRecord.transaction do"
    },
    {
      "line": 652,
      "text": "  ApplicationRecord.transaction do"
    },
    {
      "line": 736,
      "text": "- Legacy tables on `gitlab_ci` belonging to the Main or Sec Databases."
    },
    {
      "line": 745,
      "text": "for both `gitlab_main` and `gitlab_ci` tables, then no tables will be locked."
    },
    {
      "line": 811,
      "text": "When separate databases from `main` are fully split, we can free up disk"
    }
  ]
}
```

### Fonte `gl-ci-model`

```json
{
  "id": "gl-ci-model",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "v16.0.0",
  "revision": "917d3f7ad12438a8ec7177d32114073ec479998a",
  "path": "app/models/ci/application_record.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/917d3f7ad12438a8ec7177d32114073ec479998a/app/models/ci/application_record.rb",
  "observedUTC": "2026-10-14T19:47:50.012134+00:00",
  "HTTPstatus": 200,
  "sha256": "b2aef16f98a49e89695cf6755215cb03dea1372df508bcfcc6e1df1bb1a85230",
  "line_count": 19,
  "matches": [
    {
      "line": 5,
      "text": "    self.abstract_class = true"
    },
    {
      "line": 8,
      "text": "      connects_to database: { writing: :ci, reading: :ci }"
    }
  ]
}
```

### Fonte `gl-gitaly`

```json
{
  "id": "gl-gitaly",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "lib/gitlab/gitaly_client/operation_service.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/gitaly_client/operation_service.rb",
  "observedUTC": "2026-10-14T19:47:50.012290+00:00",
  "HTTPstatus": 200,
  "sha256": "e9f61947ed06c6e84e89510a66034fdf657b8ad1f08b1870025ea0f64985d28d",
  "line_count": 777,
  "matches": [
    {
      "line": 29,
      "text": "        response = gitaly_client_call(@repository.storage, :operation_service, :user_delete_tag, request, timeout: GitalyClient.long_timeout)"
    },
    {
      "line": 46,
      "text": "        response = gitaly_client_call(@repository.storage, :operation_service, :user_create_tag, request, timeout: GitalyClient.long_timeout)"
    },
    {
      "line": 49,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 85,
      "text": "        response = gitaly_client_call(@repository.storage, :operation_service,"
    },
    {
      "line": 93,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 118,
      "text": "        response = gitaly_client_call(@repository.storage, :operation_service,"
    },
    {
      "line": 134,
      "text": "        gitaly_client_call(@repository.storage, :operation_service,"
    },
    {
      "line": 138,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 164,
      "text": "        response = gitaly_client_call(@repository.storage, :operation_service,"
    },
    {
      "line": 168,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 216,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 262,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 317,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 372,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 438,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 466,
      "text": "        response = gitaly_client_call(@repository.storage, :operation_service,"
    },
    {
      "line": 493,
      "text": "      rescue GRPC::BadStatus => e"
    },
    {
      "line": 533,
      "text": "      rescue GRPC::BadStatus => e"
    }
  ]
}
```

### Fonte `modular-doc`

```json
{
  "id": "modular-doc",
  "repo": "kgrzybek/modular-monolith-with-ddd",
  "requested_ref": "master",
  "revision": "91c8ef24b4cb6ef558c95d8267fa07d68c7059f8",
  "path": "README.md",
  "url": "https://github.com/kgrzybek/modular-monolith-with-ddd/blob/91c8ef24b4cb6ef558c95d8267fa07d68c7059f8/README.md",
  "observedUTC": "2026-10-14T19:47:50.012917+00:00",
  "HTTPstatus": 200,
  "sha256": "f499f28f3736b088dea53f4a83be573aa6224e0b2bb3d34501752f5d49d15e2e",
  "line_count": 2308,
  "matches": [
    {
      "line": 343,
      "text": "2. API communicates with Modules using a small interface to send Queries and Commands"
    },
    {
      "line": 344,
      "text": "3. Each Module has its own interface which is used by API"
    },
    {
      "line": 346,
      "text": "5. Each Module **has it's own data** in a separate schema - shared data is not allowed"
    },
    {
      "line": 349,
      "text": "7. Each Module has its own [Composition Root](https://freecontent.manning.com/dependency-injection-in-net-2nd-edition-understanding-the-composition-root/), which implies that each Module has its own I"
    },
    {
      "line": 351,
      "text": "9. Each Module is **highly encapsulated** - only required types and members are public, the rest are internal or private"
    },
    {
      "line": 357,
      "text": "Each Module has [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) and consists of the following submodules (assemblies):"
    },
    {
      "line": 395,
      "text": "Each module has the same interface signature exposed to the API. It contains 3 methods: command with result, command without result and query."
    },
    {
      "line": 398,
      "text": "public interface IMeetingsModule"
    },
    {
      "line": 481,
      "text": "- Supports [Interface Segregation Principle](https://en.wikipedia.org/wiki/Interface_segregation_principle) (ISP) - each handler implements interface with exactly one method"
    },
    {
      "line": 825,
      "text": "Authentication is implemented using JWT Token and Bearer scheme using IdentityServer. For now, only one authentication method is implemented: forms style authentication (username and password) via the"
    },
    {
      "line": 2046,
      "text": "- [Autofac](https://autofac.org/) (Inversion of Control Container)"
    },
    {
      "line": 2055,
      "text": "- [MediatR](https://github.com/jbogard/MediatR) (mediator implementation)"
    }
  ]
}
```

### Fonte `pgcham-mysql`

```json
{
  "id": "pgcham-mysql",
  "repo": "the4thdoctor/pg_chameleon",
  "requested_ref": "master",
  "revision": null,
  "path": "pg_chameleon/lib/mysql_lib.py",
  "url": "https://github.com/the4thdoctor/pg_chameleon/blob/master/pg_chameleon/lib/mysql_lib.py",
  "observedUTC": "2026-10-14T19:47:50.014684+00:00",
  "HTTPstatus": 200,
  "sha256": "a948777ad32eed5af65afff8246c2bc54ece526ae4f43e75803205af3aa41fe7",
  "line_count": 1599,
  "matches": [
    {
      "line": 7,
      "text": "from pymysqlreplication import BinLogStreamReader"
    },
    {
      "line": 1223,
      "text": "        and manages them accordingly. The BinLogStreamReader function is called with the only_event parameter which"
    },
    {
      "line": 1273,
      "text": "        my_stream = BinLogStreamReader("
    },
    {
      "line": 1499,
      "text": "    def read_replica(self):"
    },
    {
      "line": 1554,
      "text": "    def init_replica(self):"
    }
  ]
}
```

### Fonte `pgcham-postgres`

```json
{
  "id": "pgcham-postgres",
  "repo": "the4thdoctor/pg_chameleon",
  "requested_ref": "master",
  "revision": null,
  "path": "pg_chameleon/lib/pg_lib.py",
  "url": "https://github.com/the4thdoctor/pg_chameleon/blob/master/pg_chameleon/lib/pg_lib.py",
  "observedUTC": "2026-10-14T19:47:50.271883+00:00",
  "HTTPstatus": 200,
  "sha256": "bc2853e4739242ef50db2efaacdc1ed4eac550f4810be2d6d8dedee5985df2e7",
  "line_count": 4218,
  "matches": [
    {
      "line": 728,
      "text": "    def detach_replica(self):"
    },
    {
      "line": 730,
      "text": "            The method detach the replica from mysql, resets all the sequences and creates the foreign keys"
    },
    {
      "line": 774,
      "text": "            self.create_foreign_keys()"
    },
    {
      "line": 777,
      "text": "    def create_foreign_keys(self):"
    },
    {
      "line": 3381,
      "text": "                    self.__create_foreign_keys()"
    },
    {
      "line": 3615,
      "text": "    def __create_foreign_keys(self):"
    },
    {
      "line": 3644,
      "text": "            The foreign key creation is managed by __create_foreign_keys() which is executed when the replica reaches the"
    }
  ]
}
```

### Fonte `pgcham-doc`

```json
{
  "id": "pgcham-doc",
  "repo": "the4thdoctor/pg_chameleon",
  "requested_ref": "master",
  "revision": null,
  "path": "README.rst",
  "url": "https://github.com/the4thdoctor/pg_chameleon/blob/master/README.rst",
  "observedUTC": "2026-10-14T19:47:50.291798+00:00",
  "HTTPstatus": 200,
  "sha256": "7b47ad986318b0c0b25b5eaaaacfc91475f1fdbd954e0414a5c41809affd4956",
  "line_count": 155,
  "matches": [
    {
      "line": 21,
      "text": "The system use the library mysql-replication to pull the row images from MySQL which are stored into PostgreSQL as JSONB."
    },
    {
      "line": 41,
      "text": "* `mysql-replication <https://pypi.python.org/pypi/mysql-replication>`_"
    },
    {
      "line": 67,
      "text": "* Migrations"
    },
    {
      "line": 81,
      "text": "* Detach replica from MySQL for migration support."
    },
    {
      "line": 83,
      "text": "* Daemonised init_replica process."
    },
    {
      "line": 87,
      "text": "* Minimal locking during init_replica for transactional engines (e.g. innodb)"
    },
    {
      "line": 95,
      "text": "The replica requires the tables to have a primary or unique key. Tables without primary/unique key are initialised during the init_replica process but not replicated."
    },
    {
      "line": 105,
      "text": "The detach replica process resets the sequences in postgres to let the database work standalone. The foreign keys from the source MySQL schema are extracted and created initially as NOT VALID.  The fo"
    }
  ]
}
```

### Fonte `istio-mirror`

```json
{
  "id": "istio-mirror",
  "repo": "istio/istio.io",
  "requested_ref": "master",
  "revision": "25007a0c275dcbdd41cadcad8569f1e9cb447d82",
  "path": "content/en/docs/tasks/traffic-management/mirroring/index.md",
  "url": "https://github.com/istio/istio.io/blob/25007a0c275dcbdd41cadcad8569f1e9cb447d82/content/en/docs/tasks/traffic-management/mirroring/index.md",
  "observedUTC": "2026-10-14T19:47:50.366078+00:00",
  "HTTPstatus": 200,
  "sha256": "762a4bd772ca5060b49d9a496956308e73d0cb31b9e00e618bdf703c61dd3dc8",
  "line_count": 407,
  "matches": [
    {
      "line": 39,
      "text": "    1. Deploy `httpbin-v1`:"
    },
    {
      "line": 44,
      "text": "        kind: Deployment"
    },
    {
      "line": 46,
      "text": "          name: httpbin-v1"
    },
    {
      "line": 69,
      "text": "    1. Deploy `httpbin-v2`:"
    },
    {
      "line": 74,
      "text": "        kind: Deployment"
    },
    {
      "line": 76,
      "text": "          name: httpbin-v2"
    },
    {
      "line": 124,
      "text": "    kind: Deployment"
    },
    {
      "line": 169,
      "text": "            subset: v1"
    },
    {
      "line": 197,
      "text": "      name: httpbin-v1"
    },
    {
      "line": 209,
      "text": "      name: httpbin-v2"
    },
    {
      "line": 230,
      "text": "        - name: httpbin-v1"
    },
    {
      "line": 259,
      "text": "1. Check the logs from `httpbin-v1` and `httpbin-v2` pods. You should see access log entries for `v1` and none for `v2`:"
    },
    {
      "line": 262,
      "text": "    $ kubectl logs deploy/httpbin-v1 -c httpbin"
    },
    {
      "line": 267,
      "text": "    $ kubectl logs deploy/httpbin-v2 -c httpbin"
    },
    {
      "line": 271,
      "text": "## Mirroring traffic to `httpbin-v2`"
    },
    {
      "line": 273,
      "text": "1. Change the route rule to mirror traffic to `httpbin-v2`:"
    },
    {
      "line": 292,
      "text": "            subset: v1"
    },
    {
      "line": 294,
      "text": "        mirror:"
    }
  ]
}
```

### Fonte `istio-ab`

```json
{
  "id": "istio-ab",
  "repo": "istio/istio",
  "requested_ref": "master",
  "revision": "4e2c1c576e33a7b411ee7f38ac4bb9dd45c36631",
  "path": "samples/bookinfo/networking/virtual-service-reviews-test-v2.yaml",
  "url": "https://github.com/istio/istio/blob/4e2c1c576e33a7b411ee7f38ac4bb9dd45c36631/samples/bookinfo/networking/virtual-service-reviews-test-v2.yaml",
  "observedUTC": "2026-10-14T19:47:50.372565+00:00",
  "HTTPstatus": 200,
  "sha256": "06051d0c916604161bb7fcccc2158e0aa2d565f51486f09d9837d0335bd04d9d",
  "line_count": 20,
  "matches": [
    {
      "line": 11,
      "text": "        end-user:"
    },
    {
      "line": 12,
      "text": "          exact: jason"
    },
    {
      "line": 16,
      "text": "        subset: v2"
    },
    {
      "line": 20,
      "text": "        subset: v1"
    }
  ]
}
```

### Fonte `roll-blue`

```json
{
  "id": "roll-blue",
  "repo": "argoproj/rollouts-demo",
  "requested_ref": "master",
  "revision": "4e8c844fe9e23b7586f95b5f6b5365693cf318ad",
  "path": "examples/blue-green/bluegreen-rollout.yaml",
  "url": "https://github.com/argoproj/rollouts-demo/blob/4e8c844fe9e23b7586f95b5f6b5365693cf318ad/examples/blue-green/bluegreen-rollout.yaml",
  "observedUTC": "2026-10-14T19:47:50.372782+00:00",
  "HTTPstatus": 200,
  "sha256": "ecee6f0aa672b7988c7b987f3d25b185d486fc6547bb7442e833064a6fe5fc34",
  "line_count": 34,
  "matches": [
    {
      "line": 2,
      "text": "kind: Rollout"
    },
    {
      "line": 31,
      "text": "    blueGreen:"
    },
    {
      "line": 32,
      "text": "      autoPromotionEnabled: false"
    },
    {
      "line": 33,
      "text": "      activeService: bluegreen-demo"
    },
    {
      "line": 34,
      "text": "      previewService: bluegreen-demo-preview"
    }
  ]
}
```

### Fonte `roll-canary`

```json
{
  "id": "roll-canary",
  "repo": "argoproj/rollouts-demo",
  "requested_ref": "master",
  "revision": "4e8c844fe9e23b7586f95b5f6b5365693cf318ad",
  "path": "examples/canary/canary-rollout.yaml",
  "url": "https://github.com/argoproj/rollouts-demo/blob/4e8c844fe9e23b7586f95b5f6b5365693cf318ad/examples/canary/canary-rollout.yaml",
  "observedUTC": "2026-10-14T19:47:50.372894+00:00",
  "HTTPstatus": 200,
  "sha256": "cd8a07247ce2a80478abb0e2259d2efa12c3db34416921fb9ad31054f25388e3",
  "line_count": 39,
  "matches": [
    {
      "line": 2,
      "text": "kind: Rollout"
    },
    {
      "line": 29,
      "text": "    canary:"
    },
    {
      "line": 32,
      "text": "      - setWeight: 20"
    },
    {
      "line": 33,
      "text": "      - pause: {}"
    },
    {
      "line": 34,
      "text": "      - setWeight: 40"
    },
    {
      "line": 35,
      "text": "      - pause: {duration: 10}"
    },
    {
      "line": 36,
      "text": "      - setWeight: 60"
    },
    {
      "line": 37,
      "text": "      - pause: {duration: 10}"
    },
    {
      "line": 38,
      "text": "      - setWeight: 80"
    },
    {
      "line": 39,
      "text": "      - pause: {duration: 10}"
    }
  ]
}
```

### Fonte `roll-analysis`

```json
{
  "id": "roll-analysis",
  "repo": "argoproj/argo-rollouts",
  "requested_ref": "master",
  "revision": "ee7e28a1365553a3d2563a2c11ffea5ec0b7644a",
  "path": "rollout/analysis.go",
  "url": "https://github.com/argoproj/argo-rollouts/blob/ee7e28a1365553a3d2563a2c11ffea5ec0b7644a/rollout/analysis.go",
  "observedUTC": "2026-10-14T19:47:50.420323+00:00",
  "HTTPstatus": 200,
  "sha256": "a5181c47e2b04028baebc33e7734c20a37b300f710b033546c3410a68fb92c3a",
  "line_count": 569,
  "matches": [
    {
      "line": 73,
      "text": "func (c *rolloutContext) reconcileAnalysisRuns() error {"
    },
    {
      "line": 158,
      "text": "\t\tc.pauseContext.AddPauseCondition(v1alpha1.PauseReasonInconclusiveAnalysis)"
    },
    {
      "line": 159,
      "text": "\tcase v1alpha1.AnalysisPhaseError, v1alpha1.AnalysisPhaseFailed:"
    },
    {
      "line": 169,
      "text": "\t\tc.pauseContext.AddAbort(message)"
    },
    {
      "line": 207,
      "text": "\t\t\tif ar.Status.Phase == v1alpha1.AnalysisPhaseFailed || ar.Status.Phase == v1alpha1.AnalysisPhaseError {"
    },
    {
      "line": 378,
      "text": "\t\tc.pauseContext.AddPauseCondition(v1alpha1.PauseReasonInconclusiveAnalysis)"
    },
    {
      "line": 379,
      "text": "\tcase v1alpha1.AnalysisPhaseError, v1alpha1.AnalysisPhaseFailed:"
    },
    {
      "line": 384,
      "text": "\t\tc.pauseContext.AddAbort(message)"
    },
    {
      "line": 436,
      "text": "\t\tc.pauseContext.AddPauseCondition(v1alpha1.PauseReasonInconclusiveAnalysis)"
    },
    {
      "line": 437,
      "text": "\tcase v1alpha1.AnalysisPhaseError, v1alpha1.AnalysisPhaseFailed:"
    },
    {
      "line": 442,
      "text": "\t\tc.pauseContext.AddAbort(message)"
    }
  ]
}
```

### Fonte `boutique-tf`

```json
{
  "id": "boutique-tf",
  "repo": "GoogleCloudPlatform/microservices-demo",
  "requested_ref": "main",
  "revision": "38e7348eb289eb5b87c0c6e8cb19ced0449dc389",
  "path": "terraform/main.tf",
  "url": "https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/terraform/main.tf",
  "observedUTC": "2026-10-14T19:47:50.427264+00:00",
  "HTTPstatus": 200,
  "sha256": "ee6c0ee3c4172ab72815ae376a5349a8ce497cc93c8224ca4693fbd72fdc588e",
  "line_count": 100,
  "matches": [
    {
      "line": 29,
      "text": "  source  = \"terraform-google-modules/project-factory/google//modules/project_services\""
    },
    {
      "line": 40,
      "text": "resource \"google_container_cluster\" \"my_cluster\" {"
    },
    {
      "line": 43,
      "text": "  location = var.region"
    },
    {
      "line": 63,
      "text": "  source  = \"terraform-google-modules/gcloud/google\""
    },
    {
      "line": 76,
      "text": "resource \"null_resource\" \"apply_deployment\" {"
    },
    {
      "line": 79,
      "text": "    command     = \"kubectl apply -k ${var.filepath_manifest} -n ${var.namespace}\""
    },
    {
      "line": 98,
      "text": "    resource.null_resource.apply_deployment"
    }
  ]
}
```

### Fonte `argo-apps`

```json
{
  "id": "argo-apps",
  "repo": "argoproj/argocd-example-apps",
  "requested_ref": "master",
  "revision": "8088f4c0d970abb09e250248cc97e35623447cb5",
  "path": "apps/templates/applications.yaml",
  "url": "https://github.com/argoproj/argocd-example-apps/blob/8088f4c0d970abb09e250248cc97e35623447cb5/apps/templates/applications.yaml",
  "observedUTC": "2026-10-14T19:47:50.630778+00:00",
  "HTTPstatus": 200,
  "sha256": "de91d58a650afde4a696f4f59da3d122e95b4c6c7e7bda22a06003369ce5253d",
  "line_count": 29,
  "matches": [
    {
      "line": 4,
      "text": "kind: Application"
    },
    {
      "line": 16,
      "text": "    path: {{ .path | default .name | quote }}"
    },
    {
      "line": 17,
      "text": "    repoURL: {{ $config.spec.source.repoURL }}"
    },
    {
      "line": 18,
      "text": "    targetRevision: {{ $config.spec.source.targetRevision }}"
    },
    {
      "line": 26,
      "text": "      prune: true"
    },
    {
      "line": 27,
      "text": "      selfHeal: true"
    }
  ]
}
```

### Fonte `argo-app-values`

```json
{
  "id": "argo-app-values",
  "repo": "argoproj/argocd-example-apps",
  "requested_ref": "master",
  "revision": "8088f4c0d970abb09e250248cc97e35623447cb5",
  "path": "apps/values.yaml",
  "url": "https://github.com/argoproj/argocd-example-apps/blob/8088f4c0d970abb09e250248cc97e35623447cb5/apps/values.yaml",
  "observedUTC": "2026-10-14T19:47:50.685296+00:00",
  "HTTPstatus": 200,
  "sha256": "d33400e9d700a3deeef2f62bede26d34a03c276117f744c6897908cad1d8d37a",
  "line_count": 71,
  "matches": [
    {
      "line": 6,
      "text": "      repoURL: https://github.com/argoproj/argocd-example-apps"
    },
    {
      "line": 7,
      "text": "      targetRevision: master"
    },
    {
      "line": 10,
      "text": "  - name: applicationset"
    },
    {
      "line": 13,
      "text": "  - name: blue-green"
    },
    {
      "line": 17,
      "text": "  - name: guestbook"
    },
    {
      "line": 18,
      "text": "  - name: helm-dependency"
    },
    {
      "line": 22,
      "text": "  - name: helm-guestbook"
    },
    {
      "line": 25,
      "text": "        releaseName: helm-guestbook"
    },
    {
      "line": 26,
      "text": "  - name: helm-hooks"
    },
    {
      "line": 27,
      "text": "  - name: jsonnet-guestbook"
    },
    {
      "line": 28,
      "text": "  - name: jsonnet-guestbook-tla"
    },
    {
      "line": 29,
      "text": "  - name: kustomize-guestbook"
    },
    {
      "line": 30,
      "text": "  - name: plugin-kasane"
    },
    {
      "line": 34,
      "text": "        name: kasane"
    },
    {
      "line": 35,
      "text": "  - name: plugin-kustomized-helm"
    },
    {
      "line": 39,
      "text": "        name: kustomized-helm"
    },
    {
      "line": 40,
      "text": "  - name: plugin-nix"
    },
    {
      "line": 44,
      "text": "        name: nix"
    }
  ]
}
```

### Fonte `k8s-rs`

```json
{
  "id": "k8s-rs",
  "repo": "kubernetes/kubernetes",
  "requested_ref": "master",
  "revision": "2fb87b41a29b74e95c06b70fb61ba318fb580bf3",
  "path": "pkg/controller/deployment/sync.go",
  "url": "https://github.com/kubernetes/kubernetes/blob/2fb87b41a29b74e95c06b70fb61ba318fb580bf3/pkg/controller/deployment/sync.go",
  "observedUTC": "2026-10-14T19:47:50.706198+00:00",
  "HTTPstatus": 200,
  "sha256": "afdab25e5f9fb1cdcb6679faf6730bce94e44df67c3a4b93d0b6ad1058db5777",
  "line_count": 567,
  "matches": [
    {
      "line": 128,
      "text": "\tnewRS, err := dc.getNewReplicaSet(ctx, d, rsList, allOldRSs, createIfNotExisted)"
    },
    {
      "line": 146,
      "text": "func (dc *DeploymentController) getNewReplicaSet(ctx context.Context, d *apps.Deployment, rsList, oldRSs []*apps.ReplicaSet, createIfNotExisted bool) (*apps.ReplicaSet, error) {"
    },
    {
      "line": 198,
      "text": "\tpodTemplateSpecHash := controller.ComputeHash(&newRSTemplate, d.Status.CollisionCount)"
    },
    {
      "line": 203,
      "text": "\t// Create new ReplicaSet"
    },
    {
      "line": 232,
      "text": "\tcreatedRS, err := dc.client.AppsV1().ReplicaSets(d.Namespace).Create(ctx, &newRS, metav1.CreateOptions{})"
    }
  ]
}
```

### Fonte `airflow-api`

```json
{
  "id": "airflow-api",
  "repo": "apache/airflow",
  "requested_ref": "main",
  "revision": "df5cf9ecb567ea5752224d8376201c2c3046b64a",
  "path": "chart/templates/api-server/api-server-deployment.yaml",
  "url": "https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/api-server/api-server-deployment.yaml",
  "observedUTC": "2026-10-14T19:47:50.706646+00:00",
  "HTTPstatus": 200,
  "sha256": "5a088b686193ca7904055d0a455ed59704ade20661b92149a381a8779520270c",
  "line_count": 260,
  "matches": [
    {
      "line": 51,
      "text": "  replicas: {{ .Values.apiServer.replicas }}"
    },
    {
      "line": 57,
      "text": "    {{- if .Values.apiServer.strategy }}"
    },
    {
      "line": 58,
      "text": "      {{- toYaml .Values.apiServer.strategy | nindent 4 }}"
    },
    {
      "line": 67,
      "text": "    type: RollingUpdate"
    },
    {
      "line": 69,
      "text": "      maxSurge: 1"
    },
    {
      "line": 70,
      "text": "      maxUnavailable: 0"
    }
  ]
}
```

### Fonte `airflow-scheduler`

```json
{
  "id": "airflow-scheduler",
  "repo": "apache/airflow",
  "requested_ref": "main",
  "revision": "df5cf9ecb567ea5752224d8376201c2c3046b64a",
  "path": "chart/templates/scheduler/scheduler-deployment.yaml",
  "url": "https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/scheduler/scheduler-deployment.yaml",
  "observedUTC": "2026-10-14T19:47:50.706827+00:00",
  "HTTPstatus": 200,
  "sha256": "a1cc2e8396d2f83582dc105f2c0ed299aede3ea8561023cd298572b26ff7e99d",
  "line_count": 367,
  "matches": [
    {
      "line": 35,
      "text": "{{- $securityContext := include \"airflowPodSecurityContext\" (list .Values.scheduler .Values) }}"
    },
    {
      "line": 36,
      "text": "{{- $containerSecurityContext := include \"containerSecurityContext\" (list .Values.scheduler .Values) }}"
    },
    {
      "line": 37,
      "text": "{{- $containerSecurityContextWaitForMigrations := include \"containerSecurityContext\" (list .Values.scheduler.waitForMigrations .Values) }}"
    },
    {
      "line": 38,
      "text": "{{- $containerSecurityContextLogGroomerSidecar := include \"containerSecurityContext\" (list .Values.scheduler.logGroomerSidecar .Values) }}"
    },
    {
      "line": 62,
      "text": "  replicas: {{ .Values.scheduler.replicas }}"
    },
    {
      "line": 72,
      "text": "  {{- if and (not $stateful) .Values.scheduler.strategy }}"
    },
    {
      "line": 73,
      "text": "  strategy: {{- toYaml .Values.scheduler.strategy | nindent 4 }}"
    },
    {
      "line": 151,
      "text": "          {{- if $containerSecurityContextWaitForMigrations }}"
    },
    {
      "line": 152,
      "text": "          securityContext: {{ $containerSecurityContextWaitForMigrations | nindent 12 }}"
    },
    {
      "line": 186,
      "text": "          {{- if $containerSecurityContext }}"
    },
    {
      "line": 187,
      "text": "          securityContext: {{ $containerSecurityContext | nindent 12 }}"
    },
    {
      "line": 264,
      "text": "          {{- if $containerSecurityContextLogGroomerSidecar }}"
    },
    {
      "line": 265,
      "text": "          securityContext: {{ $containerSecurityContextLogGroomerSidecar | nindent 12 }}"
    }
  ]
}
```

### Fonte `airflow-log-role`

```json
{
  "id": "airflow-log-role",
  "repo": "apache/airflow",
  "requested_ref": "main",
  "revision": "df5cf9ecb567ea5752224d8376201c2c3046b64a",
  "path": "chart/templates/rbac/pod-log-reader-role.yaml",
  "url": "https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-role.yaml",
  "observedUTC": "2026-10-14T19:47:50.720543+00:00",
  "HTTPstatus": 200,
  "sha256": "397aa1444d575a05ec4bca8a02779e88a8e857c118d278f6f293f09e99a2263d",
  "line_count": 64,
  "matches": [
    {
      "line": 28,
      "text": "kind: Role"
    },
    {
      "line": 51,
      "text": "    resources:"
    },
    {
      "line": 53,
      "text": "    verbs:"
    },
    {
      "line": 54,
      "text": "      - \"list\""
    },
    {
      "line": 55,
      "text": "      - \"get\""
    },
    {
      "line": 59,
      "text": "    resources:"
    },
    {
      "line": 60,
      "text": "      - \"pods/log\""
    },
    {
      "line": 61,
      "text": "    verbs:"
    },
    {
      "line": 62,
      "text": "      - \"get\""
    },
    {
      "line": 63,
      "text": "      - \"list\""
    }
  ]
}
```

### Fonte `airflow-log-binding`

```json
{
  "id": "airflow-log-binding",
  "repo": "apache/airflow",
  "requested_ref": "main",
  "revision": "df5cf9ecb567ea5752224d8376201c2c3046b64a",
  "path": "chart/templates/rbac/pod-log-reader-rolebinding.yaml",
  "url": "https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-rolebinding.yaml",
  "observedUTC": "2026-10-14T19:47:50.760402+00:00",
  "HTTPstatus": 200,
  "sha256": "e846f1fb13d56769f6955d6748f51994ce024e493627bab33300a585b5c2c345",
  "line_count": 63,
  "matches": [
    {
      "line": 33,
      "text": "  name: {{ include \"airflow.fullname\" . }}-pod-log-reader-rolebinding"
    },
    {
      "line": 35,
      "text": "  name: {{ .Release.Namespace }}-{{ include \"airflow.fullname\" . }}-pod-log-reader-rolebinding"
    },
    {
      "line": 48,
      "text": "roleRef:"
    },
    {
      "line": 52,
      "text": "  name: {{ .Release.Namespace }}-{{ include \"airflow.fullname\" . }}-pod-log-reader-role"
    },
    {
      "line": 55,
      "text": "  name: {{ include \"airflow.fullname\" . }}-pod-log-reader-role"
    },
    {
      "line": 59,
      "text": "  - kind: ServiceAccount"
    }
  ]
}
```

### Fonte `airflow-values`

```json
{
  "id": "airflow-values",
  "repo": "apache/airflow",
  "requested_ref": "main",
  "revision": "df5cf9ecb567ea5752224d8376201c2c3046b64a",
  "path": "chart/values.yaml",
  "url": "https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/values.yaml",
  "observedUTC": "2026-10-14T19:47:50.890759+00:00",
  "HTTPstatus": 200,
  "sha256": "9d899674892defb8af0a88eb513f3588486af4fe7df42e2e97ef23c792c3a7de",
  "line_count": 3688,
  "matches": []
}
```

### Fonte `patroni-ha`

```json
{
  "id": "patroni-ha",
  "repo": "patroni/patroni",
  "requested_ref": "master",
  "revision": "dbee9c3523540db23232871479ddc5698a3b9435",
  "path": "patroni/ha.py",
  "url": "https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/patroni/ha.py",
  "observedUTC": "2026-10-14T19:47:50.978617+00:00",
  "HTTPstatus": 200,
  "sha256": "82b7663b198584852cdb8ec0c573cbacba6fa955fc1ffe68072b84b8d5d98f4d",
  "line_count": 2677,
  "matches": [
    {
      "line": 1952,
      "text": "                return self.follow('demoted self after trying and failing to obtain lock',"
    },
    {
      "line": 1964,
      "text": "                return self.follow('demoting self because I am not allowed to become primary',"
    },
    {
      "line": 1966,
      "text": "            return self.follow('demoting self because i am not the healthiest node',"
    },
    {
      "line": 1969,
      "text": "    def process_healthy_cluster(self) -> str:"
    },
    {
      "line": 1970,
      "text": "        if self.has_lock():"
    },
    {
      "line": 2015,
      "text": "            return self.follow('cannot be a real primary in a standby cluster',"
    },
    {
      "line": 2018,
      "text": "        return self.follow('demoting self because I do not have the lock and I was a leader',"
    },
    {
      "line": 2123,
      "text": "                                       before_shutdown=before_shutdown if self.has_lock() else None,"
    },
    {
      "line": 2124,
      "text": "                                       after_start=after_start if self.has_lock() else None)"
    },
    {
      "line": 2125,
      "text": "        if self.is_synchronous_mode() and not self.has_lock():"
    },
    {
      "line": 2161,
      "text": "            if self.has_lock(False):"
    },
    {
      "line": 2178,
      "text": "        if self.has_lock() and self.update_lock():"
    },
    {
      "line": 2222,
      "text": "            if self.has_lock():"
    },
    {
      "line": 2283,
      "text": "        if self.has_lock():"
    },
    {
      "line": 2351,
      "text": "            if self.has_lock(False) and not self.sysid_valid(self.cluster.initialize):"
    },
    {
      "line": 2354,
      "text": "            if self.has_lock(False) and not (self.cluster.config and self.cluster.config.data):"
    },
    {
      "line": 2405,
      "text": "                if self.has_lock():"
    },
    {
      "line": 2428,
      "text": "                            if self.has_lock():"
    }
  ]
}
```

### Fonte `pg-recovery`

```json
{
  "id": "pg-recovery",
  "repo": "postgres/postgres",
  "requested_ref": "master",
  "revision": "91b1872ff2de16cd353598edbc650a185e649226",
  "path": "src/backend/access/transam/xlogrecovery.c",
  "url": "https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/access/transam/xlogrecovery.c",
  "observedUTC": "2026-10-14T19:47:51.000044+00:00",
  "HTTPstatus": 200,
  "sha256": "46d15ffe351b4a46d2cb81d5862f62a3654091d38d3084425019107ae81eaebb",
  "line_count": 5105,
  "matches": [
    {
      "line": 146,
      "text": " * When StandbyModeRequested is set, standby mode was requested, i.e."
    },
    {
      "line": 147,
      "text": " * standby.signal file was present.  When StandbyMode is set, we are currently"
    },
    {
      "line": 151,
      "text": "static bool StandbyModeRequested = false;"
    },
    {
      "line": 178,
      "text": " * Local copy of SharedHotStandbyActive variable. False actually means \"not"
    },
    {
      "line": 456,
      "text": " * StandbyModeRequested and InRecovery."
    },
    {
      "line": 559,
      "text": "\t\tif (StandbyModeRequested)"
    },
    {
      "line": 715,
      "text": "\t\t\tif (StandbyModeRequested)"
    },
    {
      "line": 770,
      "text": "\t\tif (StandbyModeRequested)"
    },
    {
      "line": 1050,
      "text": "\t * If both signal files are present, standby signal file takes precedence."
    },
    {
      "line": 1053,
      "text": "\tStandbyModeRequested = false;"
    },
    {
      "line": 1057,
      "text": "\t\tStandbyModeRequested = true;"
    },
    {
      "line": 1062,
      "text": "\t\tStandbyModeRequested = false;"
    },
    {
      "line": 1072,
      "text": "\tif (StandbyModeRequested && !IsUnderPostmaster)"
    },
    {
      "line": 1090,
      "text": "\tif (StandbyModeRequested)"
    },
    {
      "line": 1113,
      "text": "\t\t!EnableHotStandby)"
    },
    {
      "line": 2254,
      "text": "\t\tXLogRecoveryCtl->SharedHotStandbyActive = true;"
    },
    {
      "line": 3235,
      "text": "\t\t\t\tif (StandbyModeRequested)"
    },
    {
      "line": 4567,
      "text": "\t\tLocalHotStandbyActive = XLogRecoveryCtl->SharedHotStandbyActive;"
    }
  ]
}
```

### Fonte `pg-guc`

```json
{
  "id": "pg-guc",
  "repo": "postgres/postgres",
  "requested_ref": "master",
  "revision": "91b1872ff2de16cd353598edbc650a185e649226",
  "path": "src/backend/utils/misc/guc_tables.c",
  "url": "https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/utils/misc/guc_tables.c",
  "observedUTC": "2026-10-14T19:47:51.035732+00:00",
  "HTTPstatus": 200,
  "sha256": "23906c4ba2e43015bf0178d7e1bbf4544d17f91858b79b7dd769f8a9f6ee3bdd",
  "line_count": 811,
  "matches": []
}
```

### Fonte `cnpg-restore`

```json
{
  "id": "cnpg-restore",
  "repo": "cloudnative-pg/cloudnative-pg",
  "requested_ref": "main",
  "revision": "0a1b0627e774f5be022e81106eb6ac90dcef7e3a",
  "path": "docs/src/samples/cluster-example-bis-restore.yaml",
  "url": "https://github.com/cloudnative-pg/cloudnative-pg/blob/0a1b0627e774f5be022e81106eb6ac90dcef7e3a/docs/src/samples/cluster-example-bis-restore.yaml",
  "observedUTC": "2026-10-14T19:47:51.036462+00:00",
  "HTTPstatus": 200,
  "sha256": "5e6859376eb775b6dffc79c1ecf28cfd490059f7a63d0d4f0b299cd7c4baa3d0",
  "line_count": 43,
  "matches": [
    {
      "line": 4,
      "text": "  name: cluster-restore"
    },
    {
      "line": 32,
      "text": "  bootstrap:"
    },
    {
      "line": 33,
      "text": "    recovery:"
    },
    {
      "line": 34,
      "text": "      volumeSnapshots:"
    },
    {
      "line": 37,
      "text": "          kind: VolumeSnapshot"
    },
    {
      "line": 41,
      "text": "          kind: VolumeSnapshot"
    }
  ]
}
```

### Fonte `capa-az-doc`

```json
{
  "id": "capa-az-doc",
  "repo": "kubernetes-sigs/cluster-api-provider-aws",
  "requested_ref": "main",
  "revision": "5ffa11af3b508eff794fba48a673cda2bbed03d6",
  "path": "docs/book/src/topics/failure-domains/control-planes.md",
  "url": "https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/5ffa11af3b508eff794fba48a673cda2bbed03d6/docs/book/src/topics/failure-domains/control-planes.md",
  "observedUTC": "2026-10-14T19:47:51.048004+00:00",
  "HTTPstatus": 200,
  "sha256": "fde6a45e6719d721cc589e45b7aaf2c5352ad8c0b09c89fff7f64b9c3082dd0a",
  "line_count": 102,
  "matches": [
    {
      "line": 3,
      "text": "By default, the control plane of a workload cluster created by CAPA will span multiple availability zones (AZs) (also referred to as \"failure domains\") when using multiple control plane nodes. This is"
    },
    {
      "line": 29,
      "text": "  failureDomain: \"1\""
    },
    {
      "line": 52,
      "text": "    - availabilityZone: us-west-2a"
    },
    {
      "line": 55,
      "text": "    - availabilityZone: us-west-2a"
    },
    {
      "line": 57,
      "text": "    - availabilityZone: us-west-2b"
    },
    {
      "line": 60,
      "text": "    - availabilityZone: us-west-2b"
    },
    {
      "line": 62,
      "text": "    - availabilityZone: us-west-2c"
    },
    {
      "line": 65,
      "text": "    - availabilityZone: us-west-2c"
    },
    {
      "line": 75,
      "text": "Once CAPA is provided with a `network` that spans multiple AZs, the KubeadmControlPlane controller will automatically distribute control plane nodes across multiple AZs. No further configuration from "
    }
  ]
}
```

### Fonte `capa-az-controller`

```json
{
  "id": "capa-az-controller",
  "repo": "kubernetes-sigs/cluster-api-provider-aws",
  "requested_ref": "main",
  "revision": "5ffa11af3b508eff794fba48a673cda2bbed03d6",
  "path": "controllers/awscluster_controller.go",
  "url": "https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/5ffa11af3b508eff794fba48a673cda2bbed03d6/controllers/awscluster_controller.go",
  "observedUTC": "2026-10-14T19:47:51.193406+00:00",
  "HTTPstatus": 200,
  "sha256": "66667576c472aaeacf6f02df2c6fc820fb25fe51c83f86bf4ed46631f1e9b0f5",
  "line_count": 549,
  "matches": [
    {
      "line": 32,
      "text": "\tctrl \"sigs.k8s.io/controller-runtime\""
    },
    {
      "line": 33,
      "text": "\t\"sigs.k8s.io/controller-runtime/pkg/client\""
    },
    {
      "line": 34,
      "text": "\t\"sigs.k8s.io/controller-runtime/pkg/controller\""
    },
    {
      "line": 35,
      "text": "\t\"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil\""
    },
    {
      "line": 36,
      "text": "\t\"sigs.k8s.io/controller-runtime/pkg/handler\""
    },
    {
      "line": 37,
      "text": "\t\"sigs.k8s.io/controller-runtime/pkg/reconcile\""
    },
    {
      "line": 38,
      "text": "\t\"sigs.k8s.io/controller-runtime/pkg/source\""
    },
    {
      "line": 421,
      "text": "\t\tfor _, az := range awsCluster.Status.Network.APIServerELB.AvailabilityZones {"
    },
    {
      "line": 429,
      "text": "\t\t\tControlPlane: ptr.To(found),"
    }
  ]
}
```

### Fonte `movr`

```json
{
  "id": "movr",
  "repo": "cockroachdb/cockroach",
  "requested_ref": "master",
  "revision": "d30c905fff79ef825adc96bcc647f1872a90f2ff",
  "path": "pkg/workload/movr/movr.go",
  "url": "https://github.com/cockroachdb/cockroach/blob/d30c905fff79ef825adc96bcc647f1872a90f2ff/pkg/workload/movr/movr.go",
  "observedUTC": "2026-10-14T19:47:51.194574+00:00",
  "HTTPstatus": 200,
  "sha256": "60a7e6c2dc847a9116598e002f4db651c97463f38fa9ce7220b8b1043d7d1500",
  "line_count": 748,
  "matches": [
    {
      "line": 27,
      "text": "// if we are not using a multi-region movr."
    },
    {
      "line": 211,
      "text": "\t\t\t`multi-region`,"
    },
    {
      "line": 213,
      "text": "\t\t\t`Whether to use the multi-region configuration for partitions.`,"
    },
    {
      "line": 219,
      "text": "\t\t\t`Whether to infer crdb_region for multi-region REGIONAL BY ROW columns using the city column."
    },
    {
      "line": 226,
      "text": "\t\t\t\"Survival goal for multi-region workloads. Supported goals: az, region.\","
    },
    {
      "line": 321,
      "text": "ALTER DATABASE %[1]s SET PRIMARY REGION \"us-east1\";"
    },
    {
      "line": 322,
      "text": "ALTER DATABASE %[1]s ADD REGION \"us-west1\";"
    },
    {
      "line": 323,
      "text": "ALTER DATABASE %[1]s ADD REGION \"europe-west1\";"
    },
    {
      "line": 324,
      "text": "ALTER DATABASE %[1]s SURVIVE %s FAILURE"
    },
    {
      "line": 371,
      "text": "\t\t\t\t\t\t\t`ALTER TABLE %s SET LOCALITY REGIONAL BY ROW`,"
    }
  ]
}
```

### Fonte `etcd-raft`

```json
{
  "id": "etcd-raft",
  "repo": "etcd-io/etcd",
  "requested_ref": "main",
  "revision": "d3c8a155909211c6681f3075802a4aacf11528b4",
  "path": "server/etcdserver/raft.go",
  "url": "https://github.com/etcd-io/etcd/blob/d3c8a155909211c6681f3075802a4aacf11528b4/server/etcdserver/raft.go",
  "observedUTC": "2026-10-14T19:47:51.287583+00:00",
  "HTTPstatus": 200,
  "sha256": "37853a3bdf903810058a335df96e96874673a5974d9e5e5adfea96d9a52bca42",
  "line_count": 453,
  "matches": [
    {
      "line": 31,
      "text": "\t\"go.etcd.io/raft/v3\""
    },
    {
      "line": 32,
      "text": "\t\"go.etcd.io/raft/v3/raftpb\""
    },
    {
      "line": 81,
      "text": "type raftNode struct {"
    },
    {
      "line": 107,
      "text": "type raftNodeConfig struct {"
    }
  ]
}
```

### Fonte `raft-quorum`

```json
{
  "id": "raft-quorum",
  "repo": "etcd-io/raft",
  "requested_ref": "main",
  "revision": "638f42739b77572b5708eb0d8a776a272ade71ed",
  "path": "quorum/majority.go",
  "url": "https://github.com/etcd-io/raft/blob/638f42739b77572b5708eb0d8a776a272ade71ed/quorum/majority.go",
  "observedUTC": "2026-10-14T19:47:51.471447+00:00",
  "HTTPstatus": 200,
  "sha256": "dbe87c11688eddab3a44c047356c3696fc5e835be19bcb7771e4cbe631e16ea0",
  "line_count": 198,
  "matches": [
    {
      "line": 15,
      "text": "package quorum"
    },
    {
      "line": 25,
      "text": "// MajorityConfig is a set of IDs that uses majority quorums to make decisions."
    },
    {
      "line": 50,
      "text": "\t\treturn \"<empty majority quorum>\""
    },
    {
      "line": 120,
      "text": "func (c MajorityConfig) CommittedIndex(l AckedIndexer) Index {"
    },
    {
      "line": 123,
      "text": "\t\t// This plays well with joint quorums which, when one half is the zero"
    },
    {
      "line": 159,
      "text": "\t// quorum. In other words, from the end of the slice, move n/2+1 to the"
    },
    {
      "line": 166,
      "text": "// a result indicating whether the vote is pending (i.e. neither a quorum of"
    },
    {
      "line": 167,
      "text": "// yes/no has been reached), won (a quorum of yes has been reached), or lost (a"
    },
    {
      "line": 168,
      "text": "// quorum of no has been reached)."
    },
    {
      "line": 169,
      "text": "func (c MajorityConfig) VoteResult(votes map[uint64]bool) VoteResult {"
    },
    {
      "line": 172,
      "text": "\t\t// handy with joint quorums because it'll make a half-populated joint"
    },
    {
      "line": 173,
      "text": "\t\t// quorum behave like a majority quorum."
    },
    {
      "line": 190,
      "text": "\tq := len(c)/2 + 1"
    }
  ]
}
```

### Fonte `raft-check`

```json
{
  "id": "raft-check",
  "repo": "etcd-io/raft",
  "requested_ref": "main",
  "revision": "638f42739b77572b5708eb0d8a776a272ade71ed",
  "path": "raft.go",
  "url": "https://github.com/etcd-io/raft/blob/638f42739b77572b5708eb0d8a776a272ade71ed/raft.go",
  "observedUTC": "2026-10-14T19:47:51.472952+00:00",
  "HTTPstatus": 200,
  "sha256": "d3d8fa573e1488e3aa35b9b997ba943454f3f357740a550d4bcc44d81975f07f",
  "line_count": 2162,
  "matches": [
    {
      "line": 413,
      "text": "\tcheckQuorum bool"
    },
    {
      "line": 460,
      "text": "\t\tcheckQuorum:                 c.CheckQuorum,"
    },
    {
      "line": 868,
      "text": "\t\tif r.checkQuorum {"
    },
    {
      "line": 891,
      "text": "func (r *raft) becomeFollower(term uint64, lead uint64) {"
    },
    {
      "line": 1103,
      "text": "\t\t\tinLease := r.checkQuorum && r.lead != None && r.electionElapsed < r.electionTimeout"
    },
    {
      "line": 1134,
      "text": "\t\tif (r.checkQuorum || r.preVote) && (m.GetType() == pb.MsgHeartbeat || m.GetType() == pb.MsgApp) {"
    },
    {
      "line": 1139,
      "text": "\t\t\t// the majority on the old term. If checkQuorum is false, this will be"
    },
    {
      "line": 1141,
      "text": "\t\t\t// higher term, but if checkQuorum is true we may not advance the term on"
    },
    {
      "line": 1282,
      "text": "\t\tif !r.trk.QuorumActive() {"
    }
  ]
}
```

### Fonte `k8-controller-election`

```json
{
  "id": "k8-controller-election",
  "repo": "kubernetes/kubernetes",
  "requested_ref": "master",
  "revision": "2fb87b41a29b74e95c06b70fb61ba318fb580bf3",
  "path": "cmd/kube-controller-manager/app/controllermanager.go",
  "url": "https://github.com/kubernetes/kubernetes/blob/2fb87b41a29b74e95c06b70fb61ba318fb580bf3/cmd/kube-controller-manager/app/controllermanager.go",
  "observedUTC": "2026-10-14T19:47:51.473746+00:00",
  "HTTPstatus": 200,
  "sha256": "2160eaf467a8e904879ebacfa3efd44ff9bdc183b63ca4ad9d7a45e99741f8fa",
  "line_count": 882,
  "matches": [
    {
      "line": 59,
      "text": "\t\"k8s.io/client-go/tools/leaderelection\""
    },
    {
      "line": 60,
      "text": "\t\"k8s.io/client-go/tools/leaderelection/resourcelock\""
    },
    {
      "line": 227,
      "text": "\tvar electionChecker *leaderelection.HealthzAdaptor"
    },
    {
      "line": 229,
      "text": "\t\telectionChecker = leaderelection.NewLeaderHealthzAdaptor(time.Second * 20)"
    },
    {
      "line": 359,
      "text": "\t\tleaseCandidate, waitForSync, err := leaderelection.NewCandidateWithConfig(leaderelection.CandidateConfig{"
    },
    {
      "line": 381,
      "text": "\t// startedLeading must be used to wrap any OnStartedLeading leader election callback."
    },
    {
      "line": 388,
      "text": "\t\t\t// It's more efficient to cancel the context at the end of OnStartedLeading to signal termination,"
    },
    {
      "line": 404,
      "text": "\t\t\tleaderelection.LeaderCallbacks{"
    },
    {
      "line": 405,
      "text": "\t\t\t\tOnStartedLeading: startedLeading(func(ctx context.Context) error {"
    },
    {
      "line": 417,
      "text": "\t\t\t\t\tlogger.Error(nil, \"leaderelection lost/stopped\")"
    },
    {
      "line": 438,
      "text": "\t\t\t\t\tleaderelection.LeaderCallbacks{"
    },
    {
      "line": 439,
      "text": "\t\t\t\t\t\tOnStartedLeading: startedLeading(func(ctx context.Context) error {"
    },
    {
      "line": 448,
      "text": "\t\t\t\t\t\t\tlogger.Error(nil, \"migration leaderelection lost/stopped\")"
    },
    {
      "line": 844,
      "text": "func leaderElectAndRun(ctx context.Context, c *config.CompletedConfig, lockIdentity string, electionChecker *leaderelection.HealthzAdaptor, resourceLock string, leaseName string, callbacks leaderelect"
    },
    {
      "line": 860,
      "text": "\tleaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{"
    }
  ]
}
```

### Fonte `k8-heartbeat`

```json
{
  "id": "k8-heartbeat",
  "repo": "kubernetes/kubernetes",
  "requested_ref": "master",
  "revision": "2fb87b41a29b74e95c06b70fb61ba318fb580bf3",
  "path": "pkg/kubelet/kubelet.go",
  "url": "https://github.com/kubernetes/kubernetes/blob/2fb87b41a29b74e95c06b70fb61ba318fb580bf3/pkg/kubelet/kubelet.go",
  "observedUTC": "2026-10-14T19:47:51.498966+00:00",
  "HTTPstatus": 200,
  "sha256": "e0f247ef45cb281166b58ba1a013dc6925023388193bd74c1f126c695b770d34",
  "line_count": 3715,
  "matches": [
    {
      "line": 1172,
      "text": "\tklet.nodeLeaseController = lease.NewController("
    },
    {
      "line": 1981,
      "text": "\t\tgo kl.nodeLeaseController.Run(context.Background())"
    }
  ]
}
```

### Fonte `cnpg-failover`

```json
{
  "id": "cnpg-failover",
  "repo": "cloudnative-pg/cloudnative-pg",
  "requested_ref": "main",
  "revision": "0a1b0627e774f5be022e81106eb6ac90dcef7e3a",
  "path": "internal/controller/replicas.go",
  "url": "https://github.com/cloudnative-pg/cloudnative-pg/blob/0a1b0627e774f5be022e81106eb6ac90dcef7e3a/internal/controller/replicas.go",
  "observedUTC": "2026-10-14T19:47:51.523711+00:00",
  "HTTPstatus": 200,
  "sha256": "7dd105c2d346b6b64575fcd8770b0440e799b48cb881e44b04481f1b54de542c",
  "line_count": 535,
  "matches": [
    {
      "line": 90,
      "text": "\treturn r.reconcileTargetPrimaryForNonReplicaCluster(ctx, cluster, status, resources)"
    },
    {
      "line": 93,
      "text": "// reconcileTargetPrimaryForNonReplicaCluster sets the name of the target primary from the Pods status if needed"
    },
    {
      "line": 95,
      "text": "func (r *ClusterReconciler) reconcileTargetPrimaryForNonReplicaCluster("
    },
    {
      "line": 118,
      "text": "\tif err := r.enforceFailoverDelay(ctx, cluster); err != nil {"
    },
    {
      "line": 136,
      "text": "\t// (if is still alive) to shut down by setting the apiv1.PendingFailoverMarker as"
    },
    {
      "line": 148,
      "text": "\t\terr := r.setPrimaryInstance(ctx, cluster, apiv1.PendingFailoverMarker)"
    },
    {
      "line": 172,
      "text": "\tif !status.AreWalReceiversDown(cluster.Status.CurrentPrimary) {"
    },
    {
      "line": 179,
      "text": "\tif cluster.Status.TargetPrimary == apiv1.PendingFailoverMarker && cluster.IsFailoverQuorumActive() {"
    },
    {
      "line": 189,
      "text": "\t// This may be tha last step of a failover if target primary is set to apiv1.PendingFailoverMarker"
    },
    {
      "line": 191,
      "text": "\tif cluster.Status.TargetPrimary == apiv1.PendingFailoverMarker {"
    },
    {
      "line": 218,
      "text": "\treturn mostAdvancedInstance.Pod.Name, r.setPrimaryInstance(ctx, cluster, mostAdvancedInstance.Pod.Name)"
    },
    {
      "line": 351,
      "text": "\t\treturn candidate.Pod.Name, r.setPrimaryInstance(ctx, cluster, candidate.Pod.Name)"
    },
    {
      "line": 384,
      "text": "\tif err := r.enforceFailoverDelay(ctx, cluster); err != nil {"
    },
    {
      "line": 392,
      "text": "\tif !status.AreWalReceiversDown(cluster.Status.CurrentPrimary) {"
    },
    {
      "line": 425,
      "text": "\treturn status.Items[0].Pod.Name, r.setPrimaryInstance(ctx, cluster, status.Items[0].Pod.Name)"
    },
    {
      "line": 448,
      "text": "// If the cluster is not in the online upgrading phase, enforceFailoverDelay will evaluate the failover delay specified"
    },
    {
      "line": 453,
      "text": "// enforceFailoverDelay checks if the cluster is in the online upgrading phase and enforces a failover delay of"
    },
    {
      "line": 454,
      "text": "// 30 seconds if it is. enforceFailoverDelay will return an error if there is an issue with evaluating the failover"
    }
  ]
}
```

### Fonte `hdfs-fence`

```json
{
  "id": "hdfs-fence",
  "repo": "apache/hadoop",
  "requested_ref": "trunk",
  "revision": "6f3d71bc35f5eaab0487283533e6057c58038ae4",
  "path": "hadoop-hdfs-project/hadoop-hdfs/src/main/java/org/apache/hadoop/hdfs/qjournal/server/Journal.java",
  "url": "https://github.com/apache/hadoop/blob/6f3d71bc35f5eaab0487283533e6057c58038ae4/hadoop-hdfs-project/hadoop-hdfs/src/main/java/org/apache/hadoop/hdfs/qjournal/server/Journal.java",
  "observedUTC": "2026-10-14T19:47:51.546994+00:00",
  "HTTPstatus": 200,
  "sha256": "be5c67ce7564ad67b9b464d93956f0e855dd76df1253958412947c1abb2fd6f3",
  "line_count": 1241,
  "matches": [
    {
      "line": 352,
      "text": "    updateLastPromisedEpoch(epoch);"
    },
    {
      "line": 367,
      "text": "  private void updateLastPromisedEpoch(long newEpoch) throws IOException {"
    },
    {
      "line": 397,
      "text": "    checkWriteRequest(reqInfo);"
    },
    {
      "line": 486,
      "text": "    if (reqInfo.getEpoch() < lastPromisedEpoch.get()) {"
    },
    {
      "line": 493,
      "text": "      updateLastPromisedEpoch(reqInfo.getEpoch());"
    },
    {
      "line": 514,
      "text": "  private synchronized void checkWriteRequest(RequestInfo reqInfo) throws IOException {"
    },
    {
      "line": 517,
      "text": "    if (reqInfo.getEpoch() != lastWriterEpoch.get()) {"
    }
  ]
}
```

### Fonte `pg-sender`

```json
{
  "id": "pg-sender",
  "repo": "postgres/postgres",
  "requested_ref": "master",
  "revision": "91b1872ff2de16cd353598edbc650a185e649226",
  "path": "src/backend/replication/walsender.c",
  "url": "https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/replication/walsender.c",
  "observedUTC": "2026-10-14T19:47:51.548567+00:00",
  "HTTPstatus": 200,
  "sha256": "135f860b0de9805429d8ce6e776f049b632aae20e41d7e9fca444926024fc951",
  "line_count": 4692,
  "matches": [
    {
      "line": 153,
      "text": " * State for WalSndWakeupRequest"
    },
    {
      "line": 286,
      "text": "static void WalSndLoop(WalSndSendDataCallback send_data);"
    },
    {
      "line": 290,
      "text": "static void XLogSendPhysical(void);"
    },
    {
      "line": 1028,
      "text": "\t\tWalSndLoop(XLogSendPhysical);"
    },
    {
      "line": 1535,
      "text": " * WalSndLoop)."
    },
    {
      "line": 1607,
      "text": "\tWalSndLoop(XLogSendLogical);"
    },
    {
      "line": 1646,
      "text": "\t * Fill out the sendtime later, just as it's done in XLogSendPhysical, but"
    },
    {
      "line": 1772,
      "text": "\t/* reactivate latch so WalSndLoop knows to continue */"
    },
    {
      "line": 1779,
      "text": " * Write the current position to the lag tracker (see XLogSendPhysical)."
    },
    {
      "line": 2101,
      "text": "\t/* reactivate latch so WalSndLoop knows to continue */"
    },
    {
      "line": 3081,
      "text": "WalSndLoop(WalSndSendDataCallback send_data)"
    },
    {
      "line": 3398,
      "text": "XLogSendPhysical(void)"
    },
    {
      "line": 3514,
      "text": "\t * after XLogFlush() runs WalSndWakeupProcessRequests(), and although that"
    },
    {
      "line": 3774,
      "text": "\t * If we're caught up and have been requested to stop, have WalSndLoop()"
    },
    {
      "line": 4081,
      "text": " * from logical walsenders (see the comment before calling WalSndWakeup() in"
    },
    {
      "line": 4088,
      "text": "WalSndWakeup(bool physical, bool logical)"
    },
    {
      "line": 4117,
      "text": "\t * WalSndWakeup()."
    },
    {
      "line": 4131,
      "text": "\t * walsenders. It makes WalSndWakeup() callers' life easy."
    }
  ]
}
```

### Fonte `pg-receiver`

```json
{
  "id": "pg-receiver",
  "repo": "postgres/postgres",
  "requested_ref": "master",
  "revision": "91b1872ff2de16cd353598edbc650a185e649226",
  "path": "src/backend/replication/walreceiver.c",
  "url": "https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/replication/walreceiver.c",
  "observedUTC": "2026-10-14T19:47:51.720387+00:00",
  "HTTPstatus": 200,
  "sha256": "dfb4fbf31d07e8a47a52a4e078b70de37d3dc32448c87ec88b3d2080d2d2d497",
  "line_count": 1653,
  "matches": [
    {
      "line": 143,
      "text": "static void XLogWalRcvWrite(char *buf, Size nbytes, XLogRecPtr recptr,"
    },
    {
      "line": 145,
      "text": "static void XLogWalRcvFlush(bool dying, TimeLineID tli);"
    },
    {
      "line": 155,
      "text": "WalReceiverMain(const void *startup_data, size_t startup_data_len)"
    },
    {
      "line": 591,
      "text": "\t\t\t\t\tXLogWalRcvFlush(false, startpointTLI);"
    },
    {
      "line": 717,
      "text": "\t\t\tXLogWalRcvFlush(false, startpointTLI);"
    },
    {
      "line": 890,
      "text": "\tXLogWalRcvFlush(true, *startpointTLI_p);"
    },
    {
      "line": 952,
      "text": "\t\t\t\tXLogWalRcvWrite(buf, len, dataStart, tli);"
    },
    {
      "line": 992,
      "text": "XLogWalRcvWrite(char *buf, Size nbytes, XLogRecPtr recptr, TimeLineID tli)"
    },
    {
      "line": 1093,
      "text": "XLogWalRcvFlush(bool dying, TimeLineID tli)"
    },
    {
      "line": 1165,
      "text": "\tXLogWalRcvFlush(false, tli);"
    }
  ]
}
```

### Fonte `boutique-frontend`

```json
{
  "id": "boutique-frontend",
  "repo": "GoogleCloudPlatform/microservices-demo",
  "requested_ref": "main",
  "revision": "38e7348eb289eb5b87c0c6e8cb19ced0449dc389",
  "path": "src/frontend/main.go",
  "url": "https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/src/frontend/main.go",
  "observedUTC": "2026-10-14T19:47:51.786703+00:00",
  "HTTPstatus": 200,
  "sha256": "b3a1476945d381773b5d3359ec894592af28e7657db2d172b4f86f03e28b4545",
  "line_count": 235,
  "matches": [
    {
      "line": 25,
      "text": "\t\"github.com/gorilla/mux\""
    },
    {
      "line": 71,
      "text": "\tcartSvcConn *grpc.ClientConn"
    },
    {
      "line": 134,
      "text": "\tmustMapEnv(&svc.cartSvcAddr, \"CART_SERVICE_ADDR\")"
    },
    {
      "line": 143,
      "text": "\tmustConnGRPC(ctx, &svc.cartSvcConn, svc.cartSvcAddr)"
    },
    {
      "line": 167,
      "text": "\thandler = ensureSessionID(handler)                 // add session ID"
    }
  ]
}
```

### Fonte `boutique-architecture`

```json
{
  "id": "boutique-architecture",
  "repo": "GoogleCloudPlatform/microservices-demo",
  "requested_ref": "main",
  "revision": "38e7348eb289eb5b87c0c6e8cb19ced0449dc389",
  "path": "README.md",
  "url": "https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/README.md",
  "observedUTC": "2026-10-14T19:47:51.946134+00:00",
  "HTTPstatus": 200,
  "sha256": "bc00f3b549458838242287afe42df006e54602dac3f7b90c5fd1c5e5432cbe8c",
  "line_count": 170,
  "matches": [
    {
      "line": 27,
      "text": "| [frontend](/src/frontend)                           | Go            | Exposes an HTTP server to serve the website. Does not require signup/login and generates session IDs for all users automatically"
    },
    {
      "line": 28,
      "text": "| [cartservice](/src/cartservice)                     | C#            | Stores the items in the user's shopping cart in Redis and retrieves it.                                                         "
    },
    {
      "line": 98,
      "text": "   cartservice-66d497c6b7-dp5jr             1/1     Running   0          2m59s"
    },
    {
      "line": 148,
      "text": "- [Use Azure Redis Cache with the Online Boutique sample on AKS](https://medium.com/p/981bd98b53f8)"
    },
    {
      "line": 151,
      "text": "- [Use Google Cloud Memorystore (Redis) with the Online Boutique sample on GKE](https://medium.com/p/82f7879a900d)"
    }
  ]
}
```

### Fonte `teleport-authz`

```json
{
  "id": "teleport-authz",
  "repo": "gravitational/teleport",
  "requested_ref": "master",
  "revision": "1283425b60ec5f60d509ba4c791183d452923ff7",
  "path": "lib/authz/permissions.go",
  "url": "https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/lib/authz/permissions.go",
  "observedUTC": "2026-10-14T19:47:51.960453+00:00",
  "HTTPstatus": 200,
  "sha256": "80c5bf75bb8361325ebd70c7be412b2364e8bdf96d7e4b8b848c5bec959eb724",
  "line_count": 2186,
  "matches": [
    {
      "line": 169,
      "text": "\tAuthorize(ctx context.Context) (*Context, error)"
    },
    {
      "line": 179,
      "text": "func (f AuthorizerFunc) Authorize(ctx context.Context) (*Context, error) {"
    },
    {
      "line": 265,
      "text": "\t// Identity holds the caller identity:"
    },
    {
      "line": 273,
      "text": "\t// UnmappedIdentity holds the original caller identity. If this is a remote"
    },
    {
      "line": 410,
      "text": "func (a *authorizer) Authorize(ctx context.Context) (authCtx *Context, err error) {"
    },
    {
      "line": 503,
      "text": "\tcase LocalUser:"
    },
    {
      "line": 504,
      "text": "\t\treturn a.authorizeLocalUser(ctx, user)"
    },
    {
      "line": 505,
      "text": "\tcase RemoteUser:"
    },
    {
      "line": 721,
      "text": "// authorizeLocalUser returns authz context based on the username"
    },
    {
      "line": 722,
      "text": "func (a *authorizer) authorizeLocalUser(ctx context.Context, u LocalUser) (*Context, error) {"
    },
    {
      "line": 2121,
      "text": "\tcase LocalUser, RemoteUser:"
    }
  ]
}
```

### Fonte `teleport-ssh`

```json
{
  "id": "teleport-ssh",
  "repo": "gravitational/teleport",
  "requested_ref": "master",
  "revision": "1283425b60ec5f60d509ba4c791183d452923ff7",
  "path": "lib/srv/regular/sshserver.go",
  "url": "https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/lib/srv/regular/sshserver.go",
  "observedUTC": "2026-10-14T19:47:51.999672+00:00",
  "HTTPstatus": 200,
  "sha256": "04d37924615f6a533e4cc8bc1e29f64534cc60a63284bdacd5a5ede511ed9de0",
  "line_count": 2717,
  "matches": [
    {
      "line": 43,
      "text": "\t\"golang.org/x/crypto/ssh\""
    },
    {
      "line": 243,
      "text": "\trouter *proxy.Router"
    },
    {
      "line": 551,
      "text": "// SetProxyMode starts this server in SSH proxying mode"
    },
    {
      "line": 552,
      "text": "func SetProxyMode(peerAddr string, clusterGetter reversetunnelclient.ClusterGetter, ap authclient.ReadProxyAccessPoint, router *proxy.Router) ServerOption {"
    },
    {
      "line": 2380,
      "text": "\tsubsys, err := newProxySubsys(ctx, scx, s, proxySubsysRequest{"
    }
  ]
}
```

### Fonte `teleport-proxy-doc`

```json
{
  "id": "teleport-proxy-doc",
  "repo": "gravitational/teleport",
  "requested_ref": "master",
  "revision": "1283425b60ec5f60d509ba4c791183d452923ff7",
  "path": "docs/pages/reference/architecture/proxy.mdx",
  "url": "https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/docs/pages/reference/architecture/proxy.mdx",
  "observedUTC": "2026-10-14T19:47:52.004980+00:00",
  "HTTPstatus": 200,
  "sha256": "f174dbb999bed3560444c164c0b672dce96c371ee796b568bce263a40da03dcd",
  "line_count": 82,
  "matches": [
    {
      "line": 4,
      "text": "description: Architecture of Teleport's identity-aware proxy service"
    },
    {
      "line": 10,
      "text": "The Teleport Proxy Service is an identity-aware proxy with a web UI. The Teleport Proxy Service "
    },
    {
      "line": 14,
      "text": "  SSH and Windows desktops using the Teleport web UI."
    },
    {
      "line": 15,
      "text": "- Intercepts traffic for multiple protocols, including SSH, Kubernetes, HTTPS, "
    },
    {
      "line": 18,
      "text": "  using reverse tunnels."
    },
    {
      "line": 36,
      "text": "target resource, for example SSH server or Desktop:"
    },
    {
      "line": 64,
      "text": "In this mode, resources behind firewall can establish reverse tunnels back to proxies."
    },
    {
      "line": 65,
      "text": "Proxies will forward client's connections to target resources via those tunnels."
    }
  ]
}
```

### Fonte `teleport-auth-doc`

```json
{
  "id": "teleport-auth-doc",
  "repo": "gravitational/teleport",
  "requested_ref": "master",
  "revision": "1283425b60ec5f60d509ba4c791183d452923ff7",
  "path": "docs/pages/reference/architecture/authorization.mdx",
  "url": "https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/docs/pages/reference/architecture/authorization.mdx",
  "observedUTC": "2026-10-14T19:47:52.075253+00:00",
  "HTTPstatus": 200,
  "sha256": "f0f9e4e91844a3340cfea214743a39d11a3af2c4e9bb14ffe8b1449f4024db09",
  "line_count": 399,
  "matches": [
    {
      "line": 87,
      "text": "Every Teleport user is assigned one or several roles that govern access to resources and Teleport's API."
    },
    {
      "line": 252,
      "text": "Every Teleport component - whether a Proxy Service instance, Auth Service"
    },
    {
      "line": 253,
      "text": "instance, or Agent - has an up-to-date copy of all roles. Teleport components"
    },
    {
      "line": 282,
      "text": "When the Proxy Service authorizes the attempt to connect to the Kubernetes cluster it interpolates"
    }
  ]
}
```

### Fonte `fga-abac`

```json
{
  "id": "fga-abac",
  "repo": "openfga/sample-stores",
  "requested_ref": "main",
  "revision": "6802b4d859d2773eea72c2315b3a9f027a2893a0",
  "path": "stores/abac-with-rebac/store.fga.yaml",
  "url": "https://github.com/openfga/sample-stores/blob/6802b4d859d2773eea72c2315b3a9f027a2893a0/stores/abac-with-rebac/store.fga.yaml",
  "observedUTC": "2026-10-14T19:47:52.077301+00:00",
  "HTTPstatus": 200,
  "sha256": "456e9a8e74c51da07701e8a184776bbaa809b8e700cbae55c2c38299d3870a7d",
  "line_count": 101,
  "matches": [
    {
      "line": 7,
      "text": "        define email_verified : [user]"
    },
    {
      "line": 12,
      "text": "        define draft : [document]"
    },
    {
      "line": 13,
      "text": "        define published : [document]"
    },
    {
      "line": 16,
      "text": "        define viewer_email_verified : email_verified from viewer"
    },
    {
      "line": 19,
      "text": "        define owner_email_verified : email_verified from owner"
    },
    {
      "line": 21,
      "text": "        define can_view : owner_email_verified or viewer_email_verified from published"
    },
    {
      "line": 22,
      "text": "        define can_edit : owner_email_verified from draft "
    },
    {
      "line": 28,
      "text": "      relation: email_verified"
    },
    {
      "line": 32,
      "text": "      relation: email_verified"
    }
  ]
}
```

### Fonte `fga-calendar`

```json
{
  "id": "fga-calendar",
  "repo": "openfga/sample-stores",
  "requested_ref": "main",
  "revision": "6802b4d859d2773eea72c2315b3a9f027a2893a0",
  "path": "stores/calendar/model.fga",
  "url": "https://github.com/openfga/sample-stores/blob/6802b4d859d2773eea72c2315b3a9f027a2893a0/stores/calendar/model.fga",
  "observedUTC": "2026-10-14T19:47:52.077406+00:00",
  "HTTPstatus": 200,
  "sha256": "cfac3a1984260f9ffa4450ea0474c32896f789ec4e03e3f0c4767f2e8033178d",
  "line_count": 60,
  "matches": [
    {
      "line": 6,
      "text": "type organization"
    },
    {
      "line": 13,
      "text": "type calendar"
    },
    {
      "line": 19,
      "text": "    define organization_viewer: viewer from organization"
    },
    {
      "line": 24,
      "text": "    define can_view: organization_viewer or can_edit"
    },
    {
      "line": 26,
      "text": "type event"
    },
    {
      "line": 28,
      "text": "    define calendar: [calendar]"
    },
    {
      "line": 33,
      "text": "    define organization_viewer: organization_viewer from calendar"
    },
    {
      "line": 37,
      "text": "    define can_view: attendee or organization_viewer or can_edit"
    },
    {
      "line": 45,
      "text": "    define can_view: can_edit"
    },
    {
      "line": 51,
      "text": "    define can_view: organization_viewer from event or organization_scheduler from event or can_delete"
    },
    {
      "line": 60,
      "text": "    define can_view: viewer from organization or can_edit"
    }
  ]
}
```

### Fonte `opa-app`

```json
{
  "id": "opa-app",
  "repo": "open-policy-agent/contrib",
  "requested_ref": "main",
  "revision": "5b21e4cb42b8b3893a3ade1cf33423336c6176e1",
  "path": "api_authz/docker/echo_server.py",
  "url": "https://github.com/open-policy-agent/contrib/blob/5b21e4cb42b8b3893a3ade1cf33423336c6176e1/api_authz/docker/echo_server.py",
  "observedUTC": "2026-10-14T19:47:52.229913+00:00",
  "HTTPstatus": 200,
  "sha256": "64ffd7d0c74a310c848bc116bdf0f18c6bcaf6841f3a99e284809d6a6c231e26",
  "line_count": 63,
  "matches": [
    {
      "line": 9,
      "text": "from flask import Flask"
    },
    {
      "line": 10,
      "text": "from flask import request"
    },
    {
      "line": 20,
      "text": "def check_auth(url, user, method, url_as_array, token):"
    },
    {
      "line": 32,
      "text": "        rsp = requests.post(url, data=json.dumps(input_dict))"
    },
    {
      "line": 37,
      "text": "    if rsp.status_code >= 300:"
    },
    {
      "line": 38,
      "text": "        logging.info(\"Error checking auth, got status %s and message: %s\", j.status_code, j.text)"
    },
    {
      "line": 58,
      "text": "    if j.get(\"allow\", False):"
    }
  ]
}
```

### Fonte `opa-policy`

```json
{
  "id": "opa-policy",
  "repo": "open-policy-agent/contrib",
  "requested_ref": "main",
  "revision": "5b21e4cb42b8b3893a3ade1cf33423336c6176e1",
  "path": "api_authz/docker/policy/example-hr.rego",
  "url": "https://github.com/open-policy-agent/contrib/blob/5b21e4cb42b8b3893a3ade1cf33423336c6176e1/api_authz/docker/policy/example-hr.rego",
  "observedUTC": "2026-10-14T19:47:52.232560+00:00",
  "HTTPstatus": 200,
  "sha256": "5c8f8e2d3dd838c473b9d1f3470f56bad784519e44d63b110b8da5b16fb48a16",
  "line_count": 13,
  "matches": [
    {
      "line": 5,
      "text": "# Allow HR members to get anyone's salary."
    },
    {
      "line": 6,
      "text": "allow if {"
    },
    {
      "line": 7,
      "text": "\tinput.method == \"GET\""
    },
    {
      "line": 8,
      "text": "\tinput.path = [\"finance\", \"salary\", _]"
    },
    {
      "line": 9,
      "text": "\tinput.user in members"
    },
    {
      "line": 13,
      "text": "members := [\"david\"]"
    }
  ]
}
```

### Fonte `keycloak-spa`

```json
{
  "id": "keycloak-spa",
  "repo": "keycloak/keycloak-quickstarts",
  "requested_ref": "latest",
  "revision": "0a172493a5797c3b5804bbfa0799f88c0f9d7331",
  "path": "js/spa/public/index.html",
  "url": "https://github.com/keycloak/keycloak-quickstarts/blob/0a172493a5797c3b5804bbfa0799f88c0f9d7331/js/spa/public/index.html",
  "observedUTC": "2026-10-14T19:47:52.320954+00:00",
  "HTTPstatus": 200,
  "sha256": "6831fbf4df82e50d7992015d8e38cd30ed73c9eef9cf306e279cf17b3db709f6",
  "line_count": 88,
  "matches": [
    {
      "line": 27,
      "text": "      import Keycloak from \"keycloak-js\";"
    },
    {
      "line": 43,
      "text": "          keycloak.idTokenParsed.name ||"
    },
    {
      "line": 44,
      "text": "          keycloak.idTokenParsed.preferred_username;"
    },
    {
      "line": 55,
      "text": "        output(keycloak.idTokenParsed);"
    },
    {
      "line": 61,
      "text": "          output(keycloak.tokenParsed);"
    },
    {
      "line": 67,
      "text": "          await keycloak.updateToken(-1);"
    },
    {
      "line": 68,
      "text": "          output(keycloak.idTokenParsed);"
    },
    {
      "line": 78,
      "text": "      const keycloak = new Keycloak({"
    },
    {
      "line": 84,
      "text": "      await keycloak.init({ onLoad: \"login-required\" });"
    }
  ]
}
```

### Fonte `keycloak-exchange`

```json
{
  "id": "keycloak-exchange",
  "repo": "keycloak/keycloak",
  "requested_ref": "main",
  "revision": "0b881862c6363c34ef8e08a336ae3af97628251b",
  "path": "services/src/main/java/org/keycloak/protocol/oidc/tokenexchange/StandardTokenExchangeProvider.java",
  "url": "https://github.com/keycloak/keycloak/blob/0b881862c6363c34ef8e08a336ae3af97628251b/services/src/main/java/org/keycloak/protocol/oidc/tokenexchange/StandardTokenExchangeProvider.java",
  "observedUTC": "2026-10-14T19:47:52.333911+00:00",
  "HTTPstatus": 200,
  "sha256": "dfac7cfb3a3df09118670583e4200de9c0735bf09edfd83f2667620f27bd1145",
  "line_count": 458,
  "matches": [
    {
      "line": 69,
      "text": "public class StandardTokenExchangeProvider extends AbstractTokenExchangeProvider {"
    },
    {
      "line": 122,
      "text": "        AuthenticationManager.AuthResult authResult = processSubjectToken();"
    },
    {
      "line": 126,
      "text": "    protected AuthenticationManager.AuthResult processSubjectToken() {"
    },
    {
      "line": 137,
      "text": "        AuthenticationManager.AuthResult authResult = AuthenticationManager.verifyIdentityToken(session, realm, session.getContext().getUri(), clientConnection, true, true, null,"
    },
    {
      "line": 232,
      "text": "    protected void validateAudience(AccessToken token, boolean disallowOnHolderOfTokenMismatch, List<ClientModel> targetAudienceClients) {"
    },
    {
      "line": 350,
      "text": "                    clientSessionCtx.getClientSession().getUserSession(), clientSessionCtx).generateAccessToken();"
    },
    {
      "line": 352,
      "text": "            checkRequestedAudiences(responseBuilder);"
    },
    {
      "line": 384,
      "text": "                    responseBuilder.generateIDToken().generateAccessTokenHash();"
    },
    {
      "line": 415,
      "text": "    protected void checkRequestedAudiences(TokenManager.AccessTokenResponseBuilder responseBuilder) {"
    },
    {
      "line": 416,
      "text": "        Set<String> missingAudience = TokenUtils.checkRequestedAudiences(responseBuilder.getAccessToken(), params.getAudience());"
    }
  ]
}
```

### Fonte `vault-ttl`

```json
{
  "id": "vault-ttl",
  "repo": "hashicorp/vault",
  "requested_ref": "v1.14.0",
  "revision": "13a649f860186dffe3f3a4459814d87191efc321",
  "path": "builtin/logical/database/path_creds_create.go",
  "url": "https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/builtin/logical/database/path_creds_create.go",
  "observedUTC": "2026-10-14T19:47:52.399727+00:00",
  "HTTPstatus": 200,
  "sha256": "d5d08a274567a3fcdcc337252a8fcce05b8e6d6f679e6e6a6bfa43eef2d4e2dd",
  "line_count": 288,
  "matches": [
    {
      "line": 108,
      "text": "\t\tttl, _, err := framework.CalculateTTL(b.System(), 0, role.DefaultTTL, 0, role.MaxTTL, 0, time.Time{})"
    },
    {
      "line": 117,
      "text": "\t\tnewUserReq := v5.NewUserRequest{"
    },
    {
      "line": 200,
      "text": "\t\tnewUserResp, password, err := dbi.database.NewUser(ctx, newUserReq)"
    },
    {
      "line": 220,
      "text": "\t\tresp.Secret.TTL = role.DefaultTTL"
    },
    {
      "line": 221,
      "text": "\t\tresp.Secret.MaxTTL = role.MaxTTL"
    }
  ]
}
```

### Fonte `vault-rotate`

```json
{
  "id": "vault-rotate",
  "repo": "hashicorp/vault",
  "requested_ref": "v1.14.0",
  "revision": "13a649f860186dffe3f3a4459814d87191efc321",
  "path": "builtin/logical/database/path_rotate_credentials.go",
  "url": "https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/builtin/logical/database/path_rotate_credentials.go",
  "observedUTC": "2026-10-14T19:47:52.403737+00:00",
  "HTTPstatus": 200,
  "sha256": "b3607fc23483a400bae5c09b8d8314f589c5a7d9b1343357293c583499c5032c",
  "line_count": 261,
  "matches": [
    {
      "line": 18,
      "text": "func pathRotateRootCredentials(b *databaseBackend) []*framework.Path {"
    },
    {
      "line": 38,
      "text": "\t\t\t\t\tCallback:                    b.pathRotateRootCredentialsUpdate(),"
    },
    {
      "line": 77,
      "text": "func (b *databaseBackend) pathRotateRootCredentialsUpdate() framework.OperationFunc {"
    },
    {
      "line": 135,
      "text": "\t\twalID, err := framework.PutWAL(ctx, req.Storage, rotateRootWALKey, &rotateRootCredentialsWAL{"
    },
    {
      "line": 145,
      "text": "\t\tupdateReq := v5.UpdateUserRequest{"
    },
    {
      "line": 155,
      "text": "\t\tnewConfigDetails, err := dbi.database.UpdateUser(ctx, updateReq, true)"
    },
    {
      "line": 173,
      "text": "\t\terr = framework.DeleteWAL(ctx, req.Storage, walID)"
    }
  ]
}
```

### Fonte `vault-pg`

```json
{
  "id": "vault-pg",
  "repo": "hashicorp/vault",
  "requested_ref": "v1.14.0",
  "revision": "13a649f860186dffe3f3a4459814d87191efc321",
  "path": "plugins/database/postgresql/postgresql.go",
  "url": "https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/plugins/database/postgresql/postgresql.go",
  "observedUTC": "2026-10-14T19:47:52.404594+00:00",
  "HTTPstatus": 200,
  "sha256": "861041e7d67952d7fd388e63948bacc04599d6587c1898995669bbb85807429d",
  "line_count": 559,
  "matches": [
    {
      "line": 16,
      "text": "\t\"github.com/hashicorp/vault/sdk/database/dbplugin/v5\""
    },
    {
      "line": 30,
      "text": "\tdefaultChangePasswordStatement = `"
    },
    {
      "line": 144,
      "text": "func (p *PostgreSQL) UpdateUser(ctx context.Context, req dbplugin.UpdateUserRequest) (dbplugin.UpdateUserResponse, error) {"
    },
    {
      "line": 164,
      "text": "func (p *PostgreSQL) changeUserPassword(ctx context.Context, username string, changePass *dbplugin.ChangePassword) error {"
    },
    {
      "line": 167,
      "text": "\t\tstmts = []string{defaultChangePasswordStatement}"
    }
  ]
}
```

### Fonte `vault-license`

```json
{
  "id": "vault-license",
  "repo": "hashicorp/vault",
  "requested_ref": "v1.14.0",
  "revision": "13a649f860186dffe3f3a4459814d87191efc321",
  "path": "LICENSE",
  "url": "https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/LICENSE",
  "observedUTC": "2026-10-14T19:47:52.420846+00:00",
  "HTTPstatus": 200,
  "sha256": "d6b1a865f1c8c697d343bd4e0ce61025f91898486a1f00d727f32e8644af77d3",
  "line_count": 365,
  "matches": [
    {
      "line": 3,
      "text": "Mozilla Public License, version 2.0"
    }
  ]
}
```

### Fonte `apisix-jwt`

```json
{
  "id": "apisix-jwt",
  "repo": "apache/apisix",
  "requested_ref": "master",
  "revision": "2e43b6c605566d383378a45ef1f06f3debf48a42",
  "path": "apisix/plugins/jwt-auth.lua",
  "url": "https://github.com/apache/apisix/blob/2e43b6c605566d383378a45ef1f06f3debf48a42/apisix/plugins/jwt-auth.lua",
  "observedUTC": "2026-10-14T19:47:52.539916+00:00",
  "HTTPstatus": 200,
  "sha256": "659446f7f86dd0fbd3b6df74eec06d554e6112dc3be652cb330dc8f6a753aa44",
  "line_count": 396,
  "matches": [
    {
      "line": 23,
      "text": "local ngx_decode_base64 = ngx.decode_base64"
    },
    {
      "line": 24,
      "text": "local ngx      = ngx"
    },
    {
      "line": 28,
      "text": "local ngx_re_gmatch = ngx.re.gmatch"
    },
    {
      "line": 187,
      "text": "        if ngx_decode_base64(conf.secret) == nil then"
    },
    {
      "line": 204,
      "text": "    local it, err = ngx_re_gmatch(src, cookie_key_pattern .. \"=\" .. cookie_val_pattern, \"jo\")"
    },
    {
      "line": 272,
      "text": "        return ngx_decode_base64(secret)"
    },
    {
      "line": 343,
      "text": "    if not jwt:verify_signature(auth_secret) then"
    },
    {
      "line": 353,
      "text": "    local ok, err = jwt:verify_claims(conf.claims_to_verify, {"
    },
    {
      "line": 378,
      "text": "            return 401, { message = err }"
    },
    {
      "line": 385,
      "text": "            return 401, { message = \"Invalid user authorization\"}"
    }
  ]
}
```

### Fonte `spiffe-server`

```json
{
  "id": "spiffe-server",
  "repo": "spiffe/go-spiffe",
  "requested_ref": "main",
  "revision": "77c6d2e0c1203e36804e26a02faa8f893d72e7e5",
  "path": "examples/spiffe-http/server/main.go",
  "url": "https://github.com/spiffe/go-spiffe/blob/77c6d2e0c1203e36804e26a02faa8f893d72e7e5/examples/spiffe-http/server/main.go",
  "observedUTC": "2026-10-14T19:47:52.540428+00:00",
  "HTTPstatus": 200,
  "sha256": "b50ededd88993ba4debb42059f877d8df60185e122bb7ed778249fd73d5a8741",
  "line_count": 58,
  "matches": [
    {
      "line": 11,
      "text": "\t\"github.com/spiffe/go-spiffe/v2/spiffeid\""
    },
    {
      "line": 12,
      "text": "\t\"github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig\""
    },
    {
      "line": 13,
      "text": "\t\"github.com/spiffe/go-spiffe/v2/workloadapi\""
    },
    {
      "line": 37,
      "text": "\tsource, err := workloadapi.NewX509Source(ctx, workloadapi.WithClientOptions(workloadapi.WithAddr(socketPath)))"
    },
    {
      "line": 47,
      "text": "\ttlsConfig := tlsconfig.MTLSServerConfig(source, source, tlsconfig.AuthorizeID(clientID))"
    }
  ]
}
```

### Fonte `spiffe-client`

```json
{
  "id": "spiffe-client",
  "repo": "spiffe/go-spiffe",
  "requested_ref": "main",
  "revision": "77c6d2e0c1203e36804e26a02faa8f893d72e7e5",
  "path": "examples/spiffe-http/client/main.go",
  "url": "https://github.com/spiffe/go-spiffe/blob/77c6d2e0c1203e36804e26a02faa8f893d72e7e5/examples/spiffe-http/client/main.go",
  "observedUTC": "2026-10-14T19:47:52.640957+00:00",
  "HTTPstatus": 200,
  "sha256": "b749e1d555d2fa9b1e0b00b632a03dfd1442c755a641090ed25b7532792bdca3",
  "line_count": 63,
  "matches": [
    {
      "line": 10,
      "text": "\t\"github.com/spiffe/go-spiffe/v2/spiffeid\""
    },
    {
      "line": 11,
      "text": "\t\"github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig\""
    },
    {
      "line": 12,
      "text": "\t\"github.com/spiffe/go-spiffe/v2/workloadapi\""
    },
    {
      "line": 33,
      "text": "\tsource, err := workloadapi.NewX509Source(ctx, workloadapi.WithClientOptions(workloadapi.WithAddr(socketPath)))"
    },
    {
      "line": 43,
      "text": "\ttlsConfig := tlsconfig.MTLSClientConfig(source, source, tlsconfig.AuthorizeID(serverID))"
    }
  ]
}
```

### Fonte `boutique-deny-all`

```json
{
  "id": "boutique-deny-all",
  "repo": "GoogleCloudPlatform/microservices-demo",
  "requested_ref": "main",
  "revision": "38e7348eb289eb5b87c0c6e8cb19ced0449dc389",
  "path": "kustomize/components/network-policies/network-policy-deny-all.yaml",
  "url": "https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/kustomize/components/network-policies/network-policy-deny-all.yaml",
  "observedUTC": "2026-10-14T19:47:52.654045+00:00",
  "HTTPstatus": 200,
  "sha256": "b652eb906e44e1f1528744dec34cc0548403e7bef2b35ada93b289baedfe4457",
  "line_count": 23,
  "matches": [
    {
      "line": 16,
      "text": "kind: NetworkPolicy"
    },
    {
      "line": 20,
      "text": "  podSelector: {}"
    },
    {
      "line": 21,
      "text": "  policyTypes:"
    },
    {
      "line": 22,
      "text": "  - Ingress"
    },
    {
      "line": 23,
      "text": "  - Egress"
    }
  ]
}
```

### Fonte `boutique-frontend-policy`

```json
{
  "id": "boutique-frontend-policy",
  "repo": "GoogleCloudPlatform/microservices-demo",
  "requested_ref": "main",
  "revision": "38e7348eb289eb5b87c0c6e8cb19ced0449dc389",
  "path": "kustomize/components/network-policies/network-policy-frontend.yaml",
  "url": "https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/kustomize/components/network-policies/network-policy-frontend.yaml",
  "observedUTC": "2026-10-14T19:47:52.713942+00:00",
  "HTTPstatus": 200,
  "sha256": "c596bc8def5e75a06f92a63a86be84d6d592172a7348d5f9aa184348b9e7e604",
  "line_count": 29,
  "matches": [
    {
      "line": 16,
      "text": "kind: NetworkPolicy"
    },
    {
      "line": 22,
      "text": "      app: frontend"
    }
  ]
}
```

## Fontes adicionais e escolha de Multi-Region

O par final de Multi-Region usa PostgreSQL e Patroni: a documentação declara um standby cluster em outro datacenter (região), e o produto tem o caminho de acompanhamento do primário remoto. A captura candidata de MovR no HEAD não foi usada como aplicação OSS neste reparo. Vault usa exclusivamente a fonte MPL-2.0 da tag v1.14.0.

### Fonte `patroni-region`

```json
{
  "id": "patroni-region",
  "repo": "patroni/patroni",
  "requested_ref": "master",
  "revision": "dbee9c3523540db23232871479ddc5698a3b9435",
  "path": "docs/standby_cluster.rst",
  "url": "https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/docs/standby_cluster.rst",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.174731+00:00",
  "sha256": "f8aefbee4382400ca5e8e74b4d19d13f2d83907133cf5464a7821a02e2b1a605",
  "line_count": 102,
  "matches": [
    {
      "line": 1,
      "text": ".. _standby_cluster:"
    },
    {
      "line": 6,
      "text": "Patroni also support running cascading replication to a remote datacenter"
    },
    {
      "line": 7,
      "text": "(region) using a feature that is called \"standby cluster\". This type of"
    },
    {
      "line": 29,
      "text": "`standby_cluster` section. It is distinct from creating replicas, when cluster"
    },
    {
      "line": 34,
      "text": "To configure such cluster you need to specify the section ``standby_cluster``"
    },
    {
      "line": 41,
      "text": "            standby_cluster:"
    },
    {
      "line": 42,
      "text": "                host: 1.2.3.4"
    },
    {
      "line": 65,
      "text": "``standby_cluster.host`` section.  When ``standby_cluster.host`` contains"
    },
    {
      "line": 80,
      "text": "need to define a single host in the ``standby_cluster.host`` section. However,"
    }
  ]
}
```

### Fonte `patroni-multidc`

```json
{
  "id": "patroni-multidc",
  "repo": "patroni/patroni",
  "requested_ref": "master",
  "revision": "dbee9c3523540db23232871479ddc5698a3b9435",
  "path": "docs/ha_multi_dc.rst",
  "url": "https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/docs/ha_multi_dc.rst",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.175020+00:00",
  "sha256": "458d8587532d9a313f2d8e10bdfeef786bc92f27860932f08db5db5fcb23fb22",
  "line_count": 54,
  "matches": [
    {
      "line": 7,
      "text": "The high availability of a PostgreSQL cluster deployed in multiple data centers is based on replication, which can be synchronous or asynchronous (see :ref:`replication modes <replication_modes>`)."
    },
    {
      "line": 23,
      "text": "We must deploy a cluster of etcd, ZooKeeper or Consul through the different DC, with a minimum of 3 nodes, one in each zone."
    },
    {
      "line": 25,
      "text": "Regarding postgres, we must deploy at least 2 nodes, in different DC. Then you have to set ``synchronous_mode: true`` in the global :ref:`dynamic configuration <dynamic_configuration>`."
    },
    {
      "line": 32,
      "text": "With only two data centers it would be better to have two independent etcd clusters and run Patroni :ref:`standby cluster <standby_cluster>` in the second data center. If the first site is down, you c"
    },
    {
      "line": 40,
      "text": "You should not use ``pg_ctl promote`` in this scenario, you need \"manually promote\" the healthy cluster by removing ``standby_cluster`` section from the :ref:`dynamic configuration <dynamic_configurat"
    },
    {
      "line": 47,
      "text": "- Add the standby_cluster section back and it will trigger ``pg_rewind``; however, for ``pg_rewind`` to function properly, either the cluster must be initialized with ``data page checksums`` (``--data"
    }
  ]
}
```

### Fonte `modular-module`

```json
{
  "id": "modular-module",
  "repo": "kgrzybek/modular-monolith-with-ddd",
  "requested_ref": "master",
  "revision": "91c8ef24b4cb6ef558c95d8267fa07d68c7059f8",
  "path": "src/Modules/Meetings/Infrastructure/MeetingsModule.cs",
  "url": "https://github.com/kgrzybek/modular-monolith-with-ddd/blob/91c8ef24b4cb6ef558c95d8267fa07d68c7059f8/src/Modules/Meetings/Infrastructure/MeetingsModule.cs",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.175096+00:00",
  "sha256": "622c74e9f2169f72d498659a6da2a5608b2edc4d8e6d2b48a6dc2570586fc1d8",
  "line_count": 31,
  "matches": [
    {
      "line": 1,
      "text": "﻿using Autofac;"
    },
    {
      "line": 5,
      "text": "using MediatR;"
    },
    {
      "line": 9,
      "text": "    public class MeetingsModule : IMeetingsModule"
    },
    {
      "line": 25,
      "text": "                var mediator = scope.Resolve<IMediator>();"
    },
    {
      "line": 27,
      "text": "                return await mediator.Send(query);"
    }
  ]
}
```

### Fonte `gl-migration-base`

```json
{
  "id": "gl-migration-base",
  "repo": "gitlabhq/gitlabhq",
  "requested_ref": "master",
  "revision": "2b79d1b09471e0f43ace3d37ff417919a5fe7092",
  "path": "lib/gitlab/database/migration.rb",
  "url": "https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/database/migration.rb",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.175152+00:00",
  "sha256": "bd6b5992125ed596366cf35b0d36c5a3242debeec5b12189f1a5263be5bbeb9f",
  "line_count": 92,
  "matches": [
    {
      "line": 39,
      "text": "      class V1_0 < ActiveRecord::Migration[6.1]"
    }
  ]
}
```

### Fonte `pgcham-mysql-pinned`

```json
{
  "id": "pgcham-mysql-pinned",
  "repo": "the4thdoctor/pg_chameleon",
  "requested_ref": "main",
  "revision": "5458575165565b4593d33af912e7fdbeb4db49f8",
  "path": "pg_chameleon/lib/mysql_lib.py",
  "url": "https://github.com/the4thdoctor/pg_chameleon/blob/5458575165565b4593d33af912e7fdbeb4db49f8/pg_chameleon/lib/mysql_lib.py",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.941678+00:00",
  "sha256": "a948777ad32eed5af65afff8246c2bc54ece526ae4f43e75803205af3aa41fe7",
  "line_count": 1599,
  "matches": [
    {
      "line": 7,
      "text": "from pymysqlreplication import BinLogStreamReader"
    },
    {
      "line": 1223,
      "text": "        and manages them accordingly. The BinLogStreamReader function is called with the only_event parameter which"
    },
    {
      "line": 1273,
      "text": "        my_stream = BinLogStreamReader("
    },
    {
      "line": 1499,
      "text": "    def read_replica(self):"
    },
    {
      "line": 1554,
      "text": "    def init_replica(self):"
    }
  ]
}
```

### Fonte `pgcham-postgres-pinned`

```json
{
  "id": "pgcham-postgres-pinned",
  "repo": "the4thdoctor/pg_chameleon",
  "requested_ref": "main",
  "revision": "5458575165565b4593d33af912e7fdbeb4db49f8",
  "path": "pg_chameleon/lib/pg_lib.py",
  "url": "https://github.com/the4thdoctor/pg_chameleon/blob/5458575165565b4593d33af912e7fdbeb4db49f8/pg_chameleon/lib/pg_lib.py",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.916567+00:00",
  "sha256": "bc2853e4739242ef50db2efaacdc1ed4eac550f4810be2d6d8dedee5985df2e7",
  "line_count": 4218,
  "matches": [
    {
      "line": 728,
      "text": "    def detach_replica(self):"
    },
    {
      "line": 730,
      "text": "            The method detach the replica from mysql, resets all the sequences and creates the foreign keys"
    }
  ]
}
```

### Fonte `pgcham-doc-pinned`

```json
{
  "id": "pgcham-doc-pinned",
  "repo": "the4thdoctor/pg_chameleon",
  "requested_ref": "main",
  "revision": "5458575165565b4593d33af912e7fdbeb4db49f8",
  "path": "README.rst",
  "url": "https://github.com/the4thdoctor/pg_chameleon/blob/5458575165565b4593d33af912e7fdbeb4db49f8/README.rst",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.916770+00:00",
  "sha256": "7b47ad986318b0c0b25b5eaaaacfc91475f1fdbd954e0414a5c41809affd4956",
  "line_count": 155,
  "matches": [
    {
      "line": 21,
      "text": "The system use the library mysql-replication to pull the row images from MySQL which are stored into PostgreSQL as JSONB."
    },
    {
      "line": 41,
      "text": "* `mysql-replication <https://pypi.python.org/pypi/mysql-replication>`_"
    },
    {
      "line": 67,
      "text": "* Migrations"
    },
    {
      "line": 81,
      "text": "* Detach replica from MySQL for migration support."
    },
    {
      "line": 105,
      "text": "The detach replica process resets the sequences in postgres to let the database work standalone. The foreign keys from the source MySQL schema are extracted and created initially as NOT VALID.  The fo"
    }
  ]
}
```

### Fonte `httpxy-readme`

```json
{
  "id": "httpxy-readme",
  "repo": "unjs/httpxy",
  "requested_ref": "main",
  "revision": "b202844bb59ffdb3a6b84166894bcd6e3b53ffa7",
  "path": "README.md",
  "url": "https://github.com/unjs/httpxy/blob/b202844bb59ffdb3a6b84166894bcd6e3b53ffa7/README.md",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:00:56.960804+00:00",
  "sha256": "c7000806e4ffccf62f468cbdfee054c8aea46b687f04ae52826db05252390f13",
  "line_count": 266,
  "matches": [
    {
      "line": 8,
      "text": "A Full-Featured HTTP and WebSocket Proxy for Node.js"
    },
    {
      "line": 12,
      "text": "`proxyFetch` is a proxy utility with web standard (`Request`/`Response`) interfaces. It forwards requests to a specific server address (TCP host/port or Unix socket), bypassing the URL's hostname."
    },
    {
      "line": 15,
      "text": "import { proxyFetch } from \"httpxy\";"
    },
    {
      "line": 18,
      "text": "const res = await proxyFetch(\"http://127.0.0.1:3000\", \"http://example.com/api/data\");"
    },
    {
      "line": 22,
      "text": "const res2 = await proxyFetch(\"unix:/tmp/app.sock\", \"http://localhost/health\");"
    },
    {
      "line": 26,
      "text": "const res3 = await proxyFetch({ host: \"127.0.0.1\", port: 3000 }, \"http://example.com/api/data\");"
    },
    {
      "line": 34,
      "text": "const res4 = await proxyFetch(\"http://127.0.0.1:3000\", req);"
    },
    {
      "line": 37,
      "text": "const res5 = await proxyFetch(\"http://127.0.0.1:3000\", \"http://example.com/api/data\", {"
    },
    {
      "line": 48,
      "text": "`proxyUpgrade` is a standalone WebSocket upgrade proxy. It forwards `upgrade` requests to a target server without needing a `ProxyServer` instance — the WebSocket counterpart to `proxyFetch`."
    },
    {
      "line": 52,
      "text": "import { proxyUpgrade } from \"httpxy\";"
    },
    {
      "line": 55,
      "text": "  // Handle regular HTTP requests..."
    },
    {
      "line": 59,
      "text": "  proxyUpgrade(\"http://127.0.0.1:8080\", req, socket, head);"
    },
    {
      "line": 65,
      "text": "It accepts the same `addr` formats as `proxyFetch` (`\"http://host:port\"`, `\"unix:/path\"`, or `{ host, port }` / `{ socketPath }`), and returns a `Promise<Socket>` that resolves with the upstream proxy"
    },
    {
      "line": 70,
      "text": "  proxyUpgrade({ host: \"127.0.0.1\", port: 8080 }, req, socket, head, {"
    },
    {
      "line": 80,
      "text": "> Proxy server was originally forked from [http-party/node-http-proxy](https://github.com/http-party/node-http-proxy)."
    },
    {
      "line": 82,
      "text": "Create proxy:"
    },
    {
      "line": 86,
      "text": "import { createProxyServer } from \"httpxy\";"
    },
    {
      "line": 88,
      "text": "const proxy = createProxyServer({});"
    }
  ]
}
```

### Fonte `etcd-bootstrap`

```json
{
  "id": "etcd-bootstrap",
  "repo": "etcd-io/etcd",
  "revision": "d3c8a155909211c6681f3075802a4aacf11528b4",
  "path": "server/etcdserver/bootstrap.go",
  "url": "https://github.com/etcd-io/etcd/blob/d3c8a155909211c6681f3075802a4aacf11528b4/server/etcdserver/bootstrap.go",
  "HTTPstatus": 200,
  "observedUTC": "2026-10-14T20:03:23.108707+00:00",
  "sha256": "b3358279ed2d083a7b437b2272b0c9646d135d324221182d2fb596956eb58183",
  "matches": [
    {
      "line": 195,
      "text": "\tconfig  *raft.Config"
    },
    {
      "line": 564,
      "text": "func raftConfig(cfg config.ServerConfig, id uint64, s *raft.MemoryStorage) *raft.Config {"
    },
    {
      "line": 565,
      "text": "\treturn &raft.Config{"
    },
    {
      "line": 572,
      "text": "\t\tCheckQuorum:     true,"
    },
    {
      "line": 573,
      "text": "\t\tPreVote:         cfg.PreVote,"
    },
    {
      "line": 581,
      "text": "\t\tn = raft.RestartNode(b.config)"
    },
    {
      "line": 583,
      "text": "\t\tn = raft.StartNode(b.config, b.peers)"
    }
  ]
}
```

## Pares acrescentados por entrada

Cada ID da matriz abaixo recebeu seu próprio par no catálogo. A base pode ser compartilhada; o arquivo ou mecanismo da aplicação é identificado em cada entrada. As capturas de runtime mantiveram seus horários originais.

| Entry ID | Base | Papel e aplicação | Fontes primárias |
|---|---|---|---|
| `g11-e001` | [Next.js](https://github.com/vercel/next.js) e a biblioteca [httpxy](https://github.com/unjs/httpxy) | APP — Next.js server | [next-rewrites](https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/docs/01-app/03-api-reference/05-config/01-next-config-js/rewrites.mdx); [next-resolver](https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/packages/next/src/server/lib/router-utils/resolve-routes.ts); [next-proxy](https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/packages/next/src/server/lib/router-utils/proxy-request.ts); [httpxy-readme](https://github.com/unjs/httpxy/blob/b202844bb59ffdb3a6b84166894bcd6e3b53ffa7/README.md) |
| `g11-e002` | [redis-rb](https://github.com/redis/redis-rb) | APP — GitLab MultiStore | [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb); [gl-wrapper](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/wrapper.rb) |
| `g11-e003` | [redis-rb](https://github.com/redis/redis-rb) | APP — GitLab MultiStore | [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb) |
| `g11-e004` | [Istio](https://github.com/istio/istio), com proxies Envoy | REF — Istio httpbin mirroring | [istio-mirror](https://github.com/istio/istio.io/blob/25007a0c275dcbdd41cadcad8569f1e9cb447d82/content/en/docs/tasks/traffic-management/mirroring/index.md) |
| `g11-e005` | [Flipper](https://github.com/flippercloud/flipper) | APP — GitLab Redis migration | [gl-feature](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/feature.rb); [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb) |
| `g11-e006` | [Flipper](https://github.com/flippercloud/flipper) | APP — GitLab Feature | [gl-feature](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/feature.rb); [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb) |
| `g11-e007` | [ActiveRecord](https://github.com/rails/rails/tree/main/activerecord) | APP — GitLab source_xid bigint migration | [gl-expand](https://github.com/gitlabhq/gitlabhq/blob/39f78019749fcb2458260e65c987c59ca7a37a2c/db/migrate/20260114180938_initialize_conversion_of_bulk_import_entities_source_xid_to_bigint.rb); [gl-backfill](https://github.com/gitlabhq/gitlabhq/blob/39f78019749fcb2458260e65c987c59ca7a37a2c/db/post_migrate/20260114180943_backfill_bulk_import_entities_source_xid_for_bigint_conversion.rb); [gl-finalize](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260429093419_finalize_bulk_import_entities_source_xid_bigint_conversion.rb); [gl-swap](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260429093420_swap_columns_for_bulk_import_entities_source_xid_bigint_conversion.rb); [gl-cleanup](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260518124649_clean_up_bigint_conversion_for_bulk_import_entities.rb); [gl-migration-base](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/database/migration.rb) |
| `g11-e008` | [redis-rb](https://github.com/redis/redis-rb) | APP — GitLab transitional MultiStore | [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb) |
| `g11-e009` | [Autofac](https://github.com/autofac/Autofac) e MediatR | APP — modular-monolith-with-ddd | [modular-module](https://github.com/kgrzybek/modular-monolith-with-ddd/blob/91c8ef24b4cb6ef558c95d8267fa07d68c7059f8/src/Modules/Meetings/Infrastructure/MeetingsModule.cs); [modular-doc](https://github.com/kgrzybek/modular-monolith-with-ddd/blob/91c8ef24b4cb6ef558c95d8267fa07d68c7059f8/README.md) |
| `g11-e010` | [gRPC](https://github.com/grpc/grpc) | APP — GitLab Gitaly integration | [gl-gitaly](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/gitaly_client/operation_service.rb) |
| `g11-e011` | [ActiveRecord](https://github.com/rails/rails/tree/main/activerecord) | APP — GitLab multiple databases | [gl-multidb](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/doc/development/database/multiple_databases.md); [gl-ci-model](https://github.com/gitlabhq/gitlabhq/blob/917d3f7ad12438a8ec7177d32114073ec479998a/app/models/ci/application_record.rb) |
| `g11-e012` | [mysql-replication](https://pypi.org/project/mysql-replication/) | APP — pg_chameleon | [pgcham-mysql-pinned](https://github.com/the4thdoctor/pg_chameleon/blob/5458575165565b4593d33af912e7fdbeb4db49f8/pg_chameleon/lib/mysql_lib.py); [pgcham-postgres-pinned](https://github.com/the4thdoctor/pg_chameleon/blob/5458575165565b4593d33af912e7fdbeb4db49f8/pg_chameleon/lib/pg_lib.py); [pgcham-doc-pinned](https://github.com/the4thdoctor/pg_chameleon/blob/5458575165565b4593d33af912e7fdbeb4db49f8/README.rst) |
| `g11-e013` | [redis-rb](https://github.com/redis/redis-rb) | APP — GitLab MultiStore dual write | [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb) |
| `g12-e001` | [Argo Rollouts](https://github.com/argoproj/argo-rollouts) | REF — rollouts-demo BlueGreen | [roll-blue](https://github.com/argoproj/rollouts-demo/blob/4e8c844fe9e23b7586f95b5f6b5365693cf318ad/examples/blue-green/bluegreen-rollout.yaml) |
| `g12-e002` | [Argo Rollouts](https://github.com/argoproj/argo-rollouts) | REF — rollouts-demo Canary | [roll-canary](https://github.com/argoproj/rollouts-demo/blob/4e8c844fe9e23b7586f95b5f6b5365693cf318ad/examples/canary/canary-rollout.yaml) |
| `g12-e003` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Apache Airflow API chart | [airflow-api](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/api-server/api-server-deployment.yaml) |
| `g12-e004` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Apache Airflow scheduler chart | [airflow-scheduler](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/scheduler/scheduler-deployment.yaml) |
| `g12-e005` | [Istio](https://github.com/istio/istio), com proxies Envoy | REF — Istio shadow httpbin deployment | [istio-mirror](https://github.com/istio/istio.io/blob/25007a0c275dcbdd41cadcad8569f1e9cb447d82/content/en/docs/tasks/traffic-management/mirroring/index.md) |
| `g12-e006` | [Flipper](https://github.com/flippercloud/flipper) | APP — GitLab Redis dark writes | [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb); [gl-feature](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/feature.rb) |
| `g12-e007` | [Flipper](https://github.com/flippercloud/flipper) | APP — GitLab feature flag integration | [gl-feature](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/feature.rb); [gl-multistore](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/lib/gitlab/redis/multi_store.rb) |
| `g12-e008` | [Argo Rollouts](https://github.com/argoproj/argo-rollouts) | APP — Argo Rollouts analysis controller | [roll-analysis](https://github.com/argoproj/argo-rollouts/blob/ee7e28a1365553a3d2563a2c11ffea5ec0b7644a/rollout/analysis.go); [roll-canary](https://github.com/argoproj/rollouts-demo/blob/4e8c844fe9e23b7586f95b5f6b5365693cf318ad/examples/canary/canary-rollout.yaml) |
| `g12-e009` | [Istio](https://github.com/istio/istio), com proxies Envoy | REF — Istio Bookinfo variant routing | [istio-ab](https://github.com/istio/istio/blob/4e2c1c576e33a7b411ee7f38ac4bb9dd45c36631/samples/bookinfo/networking/virtual-service-reviews-test-v2.yaml) |
| `g12-e010` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Kubernetes Deployment controller | [k8s-rs](https://github.com/kubernetes/kubernetes/blob/2fb87b41a29b74e95c06b70fb61ba318fb580bf3/pkg/controller/deployment/sync.go) |
| `g12-e011` | [provider Google para Terraform](https://github.com/hashicorp/terraform-provider-google) | REF — Online Boutique Terraform | [boutique-tf](https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/terraform/main.tf) |
| `g12-e012` | [Argo CD](https://github.com/argoproj/argo-cd) | REF — argocd-example-apps | [argo-apps](https://github.com/argoproj/argocd-example-apps/blob/8088f4c0d970abb09e250248cc97e35623447cb5/apps/templates/applications.yaml); [argo-app-values](https://github.com/argoproj/argocd-example-apps/blob/8088f4c0d970abb09e250248cc97e35623447cb5/apps/values.yaml) |
| `g13-e001` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Apache Airflow API | [airflow-api](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/api-server/api-server-deployment.yaml) |
| `g13-e002` | [PostgreSQL](https://github.com/postgres/postgres) | APP — Patroni | [patroni-ha](https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/patroni/ha.py) |
| `g13-e003` | [PostgreSQL](https://github.com/postgres/postgres) | APP — PostgreSQL recovery server | [pg-recovery](https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/access/transam/xlogrecovery.c) |
| `g13-e004` | [PostgreSQL](https://github.com/postgres/postgres) | APP — PostgreSQL standby recovery | [pg-recovery](https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/access/transam/xlogrecovery.c) |
| `g13-e005` | [CloudNativePG](https://github.com/cloudnative-pg/cloudnative-pg) e PostgreSQL | REF — CNPG restore cluster | [cnpg-restore](https://github.com/cloudnative-pg/cloudnative-pg/blob/0a1b0627e774f5be022e81106eb6ac90dcef7e3a/docs/src/samples/cluster-example-bis-restore.yaml) |
| `g13-e006` | [Cluster API](https://github.com/kubernetes-sigs/cluster-api) | APP — Cluster API Provider AWS | [capa-az-doc](https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/5ffa11af3b508eff794fba48a673cda2bbed03d6/docs/book/src/topics/failure-domains/control-planes.md); [capa-az-controller](https://github.com/kubernetes-sigs/cluster-api-provider-aws/blob/5ffa11af3b508eff794fba48a673cda2bbed03d6/controllers/awscluster_controller.go) |
| `g13-e007` | [PostgreSQL](https://github.com/postgres/postgres) | APP — Patroni multi-datacenter standby cluster | [patroni-region](https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/docs/standby_cluster.rst); [patroni-multidc](https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/docs/ha_multi_dc.rst); [patroni-ha](https://github.com/patroni/patroni/blob/dbee9c3523540db23232871479ddc5698a3b9435/patroni/ha.py) |
| `g13-e008` | [biblioteca Raft do etcd](https://github.com/etcd-io/raft) | APP — etcd | [etcd-raft](https://github.com/etcd-io/etcd/blob/d3c8a155909211c6681f3075802a4aacf11528b4/server/etcdserver/raft.go); [raft-check](https://github.com/etcd-io/raft/blob/638f42739b77572b5708eb0d8a776a272ade71ed/raft.go) |
| `g13-e009` | [biblioteca Raft do etcd](https://github.com/etcd-io/raft) | APP — etcd majority quorum | [raft-quorum](https://github.com/etcd-io/raft/blob/638f42739b77572b5708eb0d8a776a272ade71ed/quorum/majority.go); [etcd-bootstrap](https://github.com/etcd-io/etcd/blob/d3c8a155909211c6681f3075802a4aacf11528b4/server/etcdserver/bootstrap.go) |
| `g13-e010` | [CloudNativePG](https://github.com/cloudnative-pg/cloudnative-pg) e PostgreSQL | APP — CloudNativePG failover controller | [cnpg-failover](https://github.com/cloudnative-pg/cloudnative-pg/blob/0a1b0627e774f5be022e81106eb6ac90dcef7e3a/internal/controller/replicas.go) |
| `g13-e011` | [CloudNativePG](https://github.com/cloudnative-pg/cloudnative-pg) e PostgreSQL | APP — CloudNativePG automatic reconciliation | [cnpg-failover](https://github.com/cloudnative-pg/cloudnative-pg/blob/0a1b0627e774f5be022e81106eb6ac90dcef7e3a/internal/controller/replicas.go) |
| `g13-e012` | [biblioteca Raft do etcd](https://github.com/etcd-io/raft) | APP — etcd quorum checking | [etcd-bootstrap](https://github.com/etcd-io/etcd/blob/d3c8a155909211c6681f3075802a4aacf11528b4/server/etcdserver/bootstrap.go); [raft-check](https://github.com/etcd-io/raft/blob/638f42739b77572b5708eb0d8a776a272ade71ed/raft.go) |
| `g13-e013` | [Quorum Journal Manager do Hadoop](https://github.com/apache/hadoop/tree/trunk/hadoop-hdfs-project/hadoop-hdfs/src/main/java/org/apache/hadoop/hdfs/qjournal/client) | APP — HDFS JournalNode | [hdfs-fence](https://github.com/apache/hadoop/blob/6f3d71bc35f5eaab0487283533e6057c58038ae4/hadoop-hdfs-project/hadoop-hdfs/src/main/java/org/apache/hadoop/hdfs/qjournal/server/Journal.java) |
| `g13-e014` | [client-go](https://github.com/kubernetes/client-go) | APP — Kubernetes Kubelet | [k8-heartbeat](https://github.com/kubernetes/kubernetes/blob/2fb87b41a29b74e95c06b70fb61ba318fb580bf3/pkg/kubelet/kubelet.go) |
| `g13-e015` | [client-go](https://github.com/kubernetes/client-go) | APP — Kubernetes controller manager | [k8-controller-election](https://github.com/kubernetes/kubernetes/blob/2fb87b41a29b74e95c06b70fb61ba318fb580bf3/cmd/kube-controller-manager/app/controllermanager.go) |
| `g13-e016` | [PostgreSQL](https://github.com/postgres/postgres) | APP — PostgreSQL streaming replication | [pg-sender](https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/replication/walsender.c); [pg-receiver](https://github.com/postgres/postgres/blob/91b1872ff2de16cd353598edbc650a185e649226/src/backend/replication/walreceiver.c) |
| `g13-e017` | [Go HTTP](https://pkg.go.dev/net/http) e gRPC | REF — Online Boutique frontend | [boutique-frontend](https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/src/frontend/main.go); [boutique-architecture](https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/README.md) |
| `g14-e001` | [Go SSH](https://pkg.go.dev/golang.org/x/crypto/ssh) | APP — Teleport identity-aware access | [teleport-authz](https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/lib/authz/permissions.go); [teleport-proxy-doc](https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/docs/pages/reference/architecture/proxy.mdx) |
| `g14-e002` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Apache Airflow security layers | [airflow-scheduler](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/scheduler/scheduler-deployment.yaml); [airflow-log-role](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-role.yaml) |
| `g14-e003` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Apache Airflow pod log reader | [airflow-log-role](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-role.yaml); [airflow-log-binding](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-rolebinding.yaml) |
| `g14-e004` | [Kubernetes](https://github.com/kubernetes/kubernetes) | APP — Apache Airflow RBAC bindings | [airflow-log-role](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-role.yaml); [airflow-log-binding](https://github.com/apache/airflow/blob/df5cf9ecb567ea5752224d8376201c2c3046b64a/chart/templates/rbac/pod-log-reader-rolebinding.yaml) |
| `g14-e005` | [OpenFGA](https://github.com/openfga/openfga) | REF — OpenFGA ABAC with ReBAC model | [fga-abac](https://github.com/openfga/sample-stores/blob/6802b4d859d2773eea72c2315b3a9f027a2893a0/stores/abac-with-rebac/store.fga.yaml) |
| `g14-e006` | [OpenFGA](https://github.com/openfga/openfga) | REF — OpenFGA calendar application model | [fga-calendar](https://github.com/openfga/sample-stores/blob/6802b4d859d2773eea72c2315b3a9f027a2893a0/stores/calendar/model.fga) |
| `g14-e007` | [OPA](https://github.com/open-policy-agent/opa) | REF — OPA Flask HTTP API authorization demo | [opa-app](https://github.com/open-policy-agent/contrib/blob/5b21e4cb42b8b3893a3ade1cf33423336c6176e1/api_authz/docker/echo_server.py); [opa-policy](https://github.com/open-policy-agent/contrib/blob/5b21e4cb42b8b3893a3ade1cf33423336c6176e1/api_authz/docker/policy/example-hr.rego) |
| `g14-e008` | [keycloak-js](https://github.com/keycloak/keycloak-js) | REF — Keycloak SPA quickstart | [keycloak-spa](https://github.com/keycloak/keycloak-quickstarts/blob/0a172493a5797c3b5804bbfa0799f88c0f9d7331/js/spa/public/index.html) |
| `g14-e009` | [keycloak-js](https://github.com/keycloak/keycloak-js) | REF — Keycloak OIDC SPA quickstart | [keycloak-spa](https://github.com/keycloak/keycloak-quickstarts/blob/0a172493a5797c3b5804bbfa0799f88c0f9d7331/js/spa/public/index.html) |
| `g14-e010` | [SPI de Token Exchange do Keycloak](https://github.com/keycloak/keycloak/tree/main/server-spi-private/src/main/java/org/keycloak/protocol/oidc) | APP — Keycloak Standard Token Exchange Provider | [keycloak-exchange](https://github.com/keycloak/keycloak/blob/0b881862c6363c34ef8e08a336ae3af97628251b/services/src/main/java/org/keycloak/protocol/oidc/tokenexchange/StandardTokenExchangeProvider.java) |
| `g14-e011` | [SDK do Vault](https://github.com/hashicorp/vault/tree/v1.14.0/sdk) | APP — Vault v1.14.0 database credentials | [vault-ttl](https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/builtin/logical/database/path_creds_create.go); [vault-pg](https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/plugins/database/postgresql/postgresql.go); [vault-license](https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/LICENSE) |
| `g14-e012` | [SDK do Vault](https://github.com/hashicorp/vault/tree/v1.14.0/sdk) | APP — Vault v1.14.0 PostgreSQL rotation | [vault-rotate](https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/builtin/logical/database/path_rotate_credentials.go); [vault-pg](https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/plugins/database/postgresql/postgresql.go); [vault-license](https://github.com/hashicorp/vault/blob/13a649f860186dffe3f3a4459814d87191efc321/LICENSE) |
| `g14-e013` | [go-spiffe](https://github.com/spiffe/go-spiffe) | REF — go-spiffe HTTP mTLS example | [spiffe-server](https://github.com/spiffe/go-spiffe/blob/77c6d2e0c1203e36804e26a02faa8f893d72e7e5/examples/spiffe-http/server/main.go); [spiffe-client](https://github.com/spiffe/go-spiffe/blob/77c6d2e0c1203e36804e26a02faa8f893d72e7e5/examples/spiffe-http/client/main.go) |
| `g14-e014` | [OpenResty](https://github.com/openresty/openresty) | APP — Apache APISIX JWT auth plugin | [apisix-jwt](https://github.com/apache/apisix/blob/2e43b6c605566d383378a45ef1f06f3debf48a42/apisix/plugins/jwt-auth.lua) |
| `g14-e015` | [go-spiffe](https://github.com/spiffe/go-spiffe) | REF — go-spiffe HTTP service identity | [spiffe-server](https://github.com/spiffe/go-spiffe/blob/77c6d2e0c1203e36804e26a02faa8f893d72e7e5/examples/spiffe-http/server/main.go); [spiffe-client](https://github.com/spiffe/go-spiffe/blob/77c6d2e0c1203e36804e26a02faa8f893d72e7e5/examples/spiffe-http/client/main.go) |
| `g14-e016` | [Go SSH](https://pkg.go.dev/golang.org/x/crypto/ssh) | APP — Teleport SSH Proxy | [teleport-ssh](https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/lib/srv/regular/sshserver.go); [teleport-proxy-doc](https://github.com/gravitational/teleport/blob/1283425b60ec5f60d509ba4c791183d452923ff7/docs/pages/reference/architecture/proxy.mdx) |
| `g14-e017` | [Kubernetes](https://github.com/kubernetes/kubernetes) | REF — Online Boutique NetworkPolicies | [boutique-deny-all](https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/kustomize/components/network-policies/network-policy-deny-all.yaml); [boutique-frontend-policy](https://github.com/GoogleCloudPlatform/microservices-demo/blob/38e7348eb289eb5b87c0c6e8cb19ced0449dc389/kustomize/components/network-policies/network-policy-frontend.yaml) |

### Hashes dos quatro catálogos

```json
[
  {
    "path": "content/referencia/catalogo/11-padroes-para-decompor-sistemas.mdx",
    "before_sha256": "7c9d6277537cbf5e27953fbd1fb760a4200664c74ab4cb17de32b9a5ddba29cc",
    "sha256": "60245767c4ea6659deb33e1ecb8be25dca48bfc70aec3a15546b2e345db1b7cf",
    "h1": "# Padrões para decompor sistemas"
  },
  {
    "path": "content/referencia/catalogo/12-deploy-e-releases.mdx",
    "before_sha256": "1150c352ab56db43907d71284da179c17e4ac25e32a9c1bef9785f024d879e00",
    "sha256": "3f279fbf7555b85c6893d48586c391a073bcce0dec1aaed2e9fb51387fe45722",
    "h1": "# Deploy e releases"
  },
  {
    "path": "content/referencia/catalogo/13-alta-disponibilidade.mdx",
    "before_sha256": "451bad235c8f5c0cbccb2daad9f6e304ccc6eb014060686e1b8f05b9538b1be7",
    "sha256": "36127277b02007a4f942f2ac372d4107410e1cfdbdf3d4fc248b4e0bfbe5f76f",
    "h1": "# Alta disponibilidade"
  },
  {
    "path": "content/referencia/catalogo/14-seguranca.mdx",
    "before_sha256": "3988a713445026162f0e69db50caece2e1cb43a0a8bf39fd3db8d72f5613f723",
    "sha256": "a3796d6b8fc46e40e5cc319f37a7bc162914e348002ecddf295a82cc8487dad0",
    "h1": "# Segurança"
  }
]
```

As fontes `airflow-values`, `pg-guc` e o candidato MovR não sustentam nenhum par final. As duas primeiras não retornaram os símbolos buscados; seus dados foram preservados como captura, sem usá-los para uma alegação. O par de Multi-Region usa o contrato explícito de Patroni para um datacenter remoto (região), não o HEAD do CockroachDB. Nenhum teste, build, deploy, falha ou restore foi executado por esta frente.

## Candidato final de 2026-10-14 20:18:11 UTC

O reparo contém 59 pares específicos: 13, 12, 17 e 17 entradas nos quatro catálogos. As leituras foram de fontes públicas e do corpus local; não houve nova medição de produção. A entrada `g11-e009` é uma **REF** MyMeetings; este é o papel final que corrige a coluna APP do mapa de trabalho acima, em concordância com o texto MDX.

O Strangler prioritário usa o produto Next.js: o resolver verifica páginas locais e o proxy httpxy encaminha o fallback ao site existente, conforme a adoção incremental declarada. O Expand/Contract prioritário usa cinco migrações pareadas de `bulk_import_entities.source_xid`: expansão, backfill, verificação, troca e limpeza.

O patch S6 da página prioritária contém somente dois hunks, para as linhas 23 e 24. A projeção dos outros 38 registros e do restante da página era `9aa05c6fd985549d1e4ea96bb574d18922d23beff9aafae80edc20cdee12ce3e` antes do patch e agora é `44e8a96d4a9f5acc84f17c1ce923ea4c2e289de9198e33df0d50499cfea2a908`. A comparação detectou edição concorrente: na leitura de 20:16:31 UTC, as linhas 15 e 19 já continham as alterações de Guava/Trino e do anchor NiFi informadas pela raiz. Esses textos foram preservados. O hash final abaixo corresponde à página inteira naquele instante, incluindo essa evolução paralela.

```json
{
  "observedUTC": "2026-10-14 20:18:11 UTC",
  "catalog_counts": [
    {
      "path": "content/referencia/catalogo/11-padroes-para-decompor-sistemas.mdx",
      "entry_ids": 13,
      "pairs": 13,
      "h1": "# Padrões para decompor sistemas"
    },
    {
      "path": "content/referencia/catalogo/12-deploy-e-releases.mdx",
      "entry_ids": 12,
      "pairs": 12,
      "h1": "# Deploy e releases"
    },
    {
      "path": "content/referencia/catalogo/13-alta-disponibilidade.mdx",
      "entry_ids": 17,
      "pairs": 17,
      "h1": "# Alta disponibilidade"
    },
    {
      "path": "content/referencia/catalogo/14-seguranca.mdx",
      "entry_ids": 17,
      "pairs": 17,
      "h1": "# Segurança"
    }
  ],
  "candidate_hashes": [
    {
      "path": "content/referencia/catalogo/11-padroes-para-decompor-sistemas.mdx",
      "sha256": "60245767c4ea6659deb33e1ecb8be25dca48bfc70aec3a15546b2e345db1b7cf"
    },
    {
      "path": "content/referencia/catalogo/12-deploy-e-releases.mdx",
      "sha256": "3f279fbf7555b85c6893d48586c391a073bcce0dec1aaed2e9fb51387fe45722"
    },
    {
      "path": "content/referencia/catalogo/13-alta-disponibilidade.mdx",
      "sha256": "36127277b02007a4f942f2ac372d4107410e1cfdbdf3d4fc248b4e0bfbe5f76f"
    },
    {
      "path": "content/referencia/catalogo/14-seguranca.mdx",
      "sha256": "a3796d6b8fc46e40e5cc319f37a7bc162914e348002ecddf295a82cc8487dad0"
    },
    {
      "path": "content/referencia/prioritarios.mdx",
      "sha256": "6d9e8d01bfb49c84a0f1302caed196d60200fe7abffd8a182d23090366a70220"
    }
  ],
  "priority_rows_repaired": [
    23,
    24
  ],
  "other38_projection_sha256": "44e8a96d4a9f5acc84f17c1ce923ea4c2e289de9198e33df0d50499cfea2a908",
  "application_role_correction": {
    "g11-e009": "REF"
  }
}
```

### Linhas prioritárias finais

| 23 | Strangler Fig | [Estudar](/explicacoes/safe-change/#pattern-23) | [Next.js](https://github.com/vercel/next.js) + [httpxy](https://github.com/unjs/httpxy) | **Produto OSS** [Next.js — páginas locais precedem o fallback ao site existente](https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/packages/next/src/server/lib/router-utils/resolve-routes.ts#L101-L115), com [proxy externo](https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/packages/next/src/server/lib/router-utils/proxy-request.ts#L24-L33) e [adoção incremental declarada](https://github.com/vercel/next.js/blob/58f4af6ab2d9142acb3d20e1b070359f608f7b35/docs/01-app/03-api-reference/05-config/01-next-config-js/rewrites.mdx); cada página migrada deixa de seguir o caminho antigo. |
| 24 | Expand/Contract | [Estudar](/explicacoes/safe-change/#pattern-24) | [ActiveRecord](https://github.com/rails/rails/tree/main/activerecord) | **Produto OSS** GitLab — `bulk_import_entities.source_xid`: [expandir](https://github.com/gitlabhq/gitlabhq/blob/39f78019749fcb2458260e65c987c59ca7a37a2c/db/migrate/20260114180938_initialize_conversion_of_bulk_import_entities_source_xid_to_bigint.rb), [backfill](https://github.com/gitlabhq/gitlabhq/blob/39f78019749fcb2458260e65c987c59ca7a37a2c/db/post_migrate/20260114180943_backfill_bulk_import_entities_source_xid_for_bigint_conversion.rb), [validar término](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260429093419_finalize_bulk_import_entities_source_xid_bigint_conversion.rb), [trocar colunas](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260429093420_swap_columns_for_bulk_import_entities_source_xid_bigint_conversion.rb) e [limpar conversão](https://github.com/gitlabhq/gitlabhq/blob/2b79d1b09471e0f43ace3d37ff417919a5fe7092/db/post_migrate/20260518124649_clean_up_bigint_conversion_for_bulk_import_entities.rb); fontes pareadas da mesma coluna, com revisão fixada. |

Não ficou uma lacuna declarada de localizador de base/aplicação nos 59 itens deste candidato. Esta é uma afirmação de autoria e inventário, não um veredito independente de R1. Implantação na Faz, execução dos exemplos, failover e restore continuam fora da evidência deste reparo. O material passa à rechecagem do reviewer; não houve testes ou build.
