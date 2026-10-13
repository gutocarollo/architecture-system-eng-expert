"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { Collection, Resource, ResourceType, Topic } from "@/lib/content";

const resourceTypes: ResourceType[] = [
  "Article",
  "Video",
  "Course",
  "Book",
  "Library",
  "Sample",
  "Tool",
  "Resource",
];

type SortOption = "relevance" | "topics" | "resources" | "name";

const typeEmojis: Record<ResourceType, string> = {
  Article: "📕",
  Video: "📺",
  Course: "🎓",
  Book: "📚",
  Library: "📦",
  Sample: "🧪",
  Tool: "🛠️",
  Resource: "📘",
};

const collectionEmojis: Record<string, string> = {
  ai: "✦",
  "anti-patterns": "⚠️",
  "architectural-design-principles": "🧭",
  azure: "☁️",
  "cloud-design-patterns": "☁️",
  database: "🗄️",
  devops: "⚙️",
  "domain-driven-design": "🧩",
  "design-patterns": "🧱",
  microservices: "◌",
  messaging: "✉️",
  modeling: "📐",
  security: "🛡️",
  "systems-design": "🕸️",
};

const fallbackCollectionEmojis = ["◈", "⬡", "✺", "⌘", "◍", "◇"];

function getCollectionEmoji(slug: string, colorIndex: number) {
  return (
    collectionEmojis[slug] ||
    fallbackCollectionEmojis[colorIndex % fallbackCollectionEmojis.length]
  );
}

function CollectionCard({
  collection,
  topics,
  colorIndex,
}: {
  collection: Collection;
  topics: Topic[];
  colorIndex: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [subCollectionsExpanded, setSubCollectionsExpanded] = useState(false);
  const typePreviews = (
    Object.entries(collection.typeCounts) as [ResourceType, number][]
  ).filter(([, count]) => count > 0);

  return (
    <article
      className={`collection-card collection-color-${colorIndex % 6}${expanded ? " expanded" : ""}`}
    >
      <Link
        className="collection-card-link"
        href={`/collections/${collection.slug}`}
      >
        <div className="collection-card-top">
          <span className="collection-icon" aria-hidden="true">
            {getCollectionEmoji(collection.slug, colorIndex)}
          </span>
          <div className="collection-card-heading">
            {collection.subCollectionCount > 0 && (
              <span className="collection-meta">
                {collection.subCollectionCount} sub-collections
              </span>
            )}
            <span className="collection-meta">
              {collection.topicCount} topics
            </span>
          </div>
        </div>
        <h3>{collection.title}</h3>
        <p>{collection.description}</p>
        <div className="collection-stats">
          <span>{collection.subCollectionCount} sub-collections</span>
          <span>{collection.topicCount} topics</span>
        </div>
      </Link>
      {collection.subCollections.length > 0 && (
        <div
          className={`collection-subgroups${subCollectionsExpanded ? " expanded" : ""}`}
        >
          <button
            className="collection-expand collection-subgroups-toggle"
            type="button"
            aria-expanded={subCollectionsExpanded}
            aria-controls={`collection-subcollections-${collection.slug}`}
            onClick={() => setSubCollectionsExpanded((value) => !value)}
          >
            <span className="collection-expand-label">
              <span className="collection-expand-icon" aria-hidden="true" />
              <span>
                {subCollectionsExpanded
                  ? "Hide sub-collections"
                  : "Browse sub-collections"}
              </span>
            </span>
            <span className="collection-expand-hint">
              {subCollectionsExpanded ? "Collapse" : "View list"}
            </span>
          </button>
          {subCollectionsExpanded && (
            <div
              className="collection-subgroups-list"
              id={`collection-subcollections-${collection.slug}`}
            >
              {collection.subCollections.map((subCollection) => {
                const subCollectionTopics = topics.filter((topic) =>
                  topic.path.startsWith(
                    `${collection.slug}/${subCollection.slug}/`,
                  ),
                );

                return (
                  <div className="collection-subgroup" key={subCollection.slug}>
                    <Link
                      className="collection-subgroup-link"
                      href={`/collections/${collection.slug}`}
                    >
                      <strong>{subCollection.title}</strong>
                      <span aria-hidden="true">↗</span>
                    </Link>
                    <span>{subCollection.topicCount} topics</span>
                    {subCollectionTopics.length > 0 && (
                      <div className="collection-subgroup-topics">
                        {subCollectionTopics.map((topic) => (
                          <Link href={`/topics/${topic.slug}`} key={topic.slug}>
                            {topic.title} <span aria-hidden="true">↗</span>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
      <button
        className="collection-expand"
        type="button"
        aria-expanded={expanded}
        aria-controls={`collection-topics-${collection.slug}`}
        onClick={() => setExpanded((value) => !value)}
      >
        <span className="collection-expand-label">
          <span className="collection-expand-icon" aria-hidden="true" />
          <span>
            {expanded ? "Hide topics" : `Browse ${topics.length} topics`}
          </span>
        </span>
        <span className="collection-expand-hint">
          {expanded ? "Collapse" : "View list"}
        </span>
      </button>
      {expanded && (
        <div
          className="collection-topic-list"
          id={`collection-topics-${collection.slug}`}
        >
          <div className="collection-topic-heading">
            <strong>Topics in collection</strong>
            <span>{topics.length} total</span>
          </div>
          <div className="collection-topic-links">
            {topics.map((topic) => (
              <Link href={`/topics/${topic.slug}`} key={topic.slug}>
                <span>
                  <span className="collection-topic-arrow" aria-hidden="true">
                    ↗
                  </span>
                  {topic.title}
                </span>
                <small>{topic.resourceCount} resources</small>
              </Link>
            ))}
          </div>
        </div>
      )}
      <div className="collection-type-list" aria-label="Resource types">
        {typePreviews.map(([type, count]) => (
          <span
            className={`collection-type type-${type.toLowerCase()}`}
            key={type}
          >
            <span className="collection-type-emoji" aria-hidden="true">
              {typeEmojis[type]}
            </span>
            <span>{type}</span>
            <strong>{count}</strong>
          </span>
        ))}
      </div>
      <Link className="card-link" href={`/collections/${collection.slug}`}>
        Open collection <span aria-hidden="true">↗</span>
      </Link>
    </article>
  );
}

export function HomeAtlas({
  collections,
  topics,
  resources,
}: {
  collections: Collection[];
  topics: Topic[];
  resources: Resource[];
}) {
  const [query, setQuery] = useState("");
  const [activeCollection, setActiveCollection] = useState("All");
  const [activeType, setActiveType] = useState<"All" | ResourceType>("All");
  const [sortBy, setSortBy] = useState<SortOption>("relevance");

  const visibleCollections = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = collections.filter((collection) => {
      if (activeCollection !== "All" && collection.slug !== activeCollection) {
        return false;
      }

      if (activeType !== "All" && collection.typeCounts[activeType] === 0) {
        return false;
      }

      if (!normalizedQuery) return true;

      const collectionTopics = topics.filter((topic) =>
        topic.path.startsWith(`${collection.slug}/`),
      );
      const topicText = collectionTopics
        .map(
          (topic) =>
            `${topic.title} ${topic.description} ${topic.sections.map((section) => section.title).join(" ")}`,
        )
        .join(" ")
        .toLowerCase();
      const resourceText = resources
        .filter((resource) =>
          resource.topicSlug.startsWith(`${collection.slug}-`),
        )
        .map(
          (resource) =>
            `${resource.title} ${resource.description} ${resource.domain}`,
        )
        .join(" ")
        .toLowerCase();

      return (
        `${collection.title} ${collection.description} ${collection.subCollections.map((subCollection) => subCollection.title).join(" ")}`
          .toLowerCase()
          .includes(normalizedQuery) ||
        topicText.includes(normalizedQuery) ||
        resourceText.includes(normalizedQuery)
      );
    });

    return [...filtered].sort((left, right) => {
      if (sortBy === "topics") return right.topicCount - left.topicCount;
      if (sortBy === "resources")
        return right.resourceCount - left.resourceCount;
      if (sortBy === "name") return left.title.localeCompare(right.title);
      return 0;
    });
  }, [
    activeCollection,
    activeType,
    collections,
    query,
    resources,
    sortBy,
    topics,
  ]);

  const hasFilters =
    query.trim() || activeCollection !== "All" || activeType !== "All";

  function resetFilters() {
    setQuery("");
    setActiveCollection("All");
    setActiveType("All");
    setSortBy("relevance");
  }

  return (
    <>
      <section className="home-search-strip" id="collections">
        <label className="atlas-search atlas-search-simple">
          <span aria-hidden="true">⌕</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search collections, topics, sections, names, source..."
          />
        </label>
        <div className="advanced-search" aria-label="Advanced search filters">
          <div className="advanced-search-group">
            <span className="advanced-search-label">Collection</span>
            <div className="atlas-filter-row">
              <button
                className={`atlas-chip tag-collection-all${activeCollection === "All" ? " active" : ""}`}
                type="button"
                aria-pressed={activeCollection === "All"}
                onClick={() => setActiveCollection("All")}
              >
                All <strong>{collections.length}</strong>
              </button>
              {collections.map((collection) => (
                <button
                  className={`atlas-chip tag-collection-${collections.indexOf(collection) % 6}${activeCollection === collection.slug ? " active" : ""}`}
                  type="button"
                  aria-pressed={activeCollection === collection.slug}
                  key={collection.slug}
                  onClick={() => setActiveCollection(collection.slug)}
                >
                  {collection.title} <strong>{collection.topicCount}</strong>
                </button>
              ))}
            </div>
          </div>
          <div className="advanced-search-group">
            <span className="advanced-search-label">Resource type</span>
            <div className="atlas-filter-row">
              <button
                className={`atlas-chip tag-all-types${activeType === "All" ? " active" : ""}`}
                type="button"
                aria-pressed={activeType === "All"}
                onClick={() => setActiveType("All")}
              >
                All types
              </button>
              {resourceTypes.map((type) => {
                const count = collections.reduce(
                  (total, collection) => total + collection.typeCounts[type],
                  0,
                );
                return (
                  <button
                    className={`atlas-chip type-${type.toLowerCase()}${activeType === type ? " active" : ""}`}
                    type="button"
                    aria-pressed={activeType === type}
                    key={type}
                    onClick={() => setActiveType(type)}
                  >
                    {type} <strong>{count}</strong>
                  </button>
                );
              })}
            </div>
          </div>
          <div className="advanced-search-footer">
            <span>
              Showing {visibleCollections.length} of {collections.length}{" "}
              collections
            </span>
            <label>
              Sort by
              <select
                value={sortBy}
                onChange={(event) =>
                  setSortBy(event.target.value as SortOption)
                }
              >
                <option value="relevance">Relevance</option>
                <option value="topics">Topics</option>
                <option value="resources">Resources</option>
                <option value="name">Name</option>
              </select>
            </label>
            {hasFilters && (
              <button
                className="filter-reset"
                type="button"
                onClick={resetFilters}
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="atlas-section" id="topics">
        <div className="atlas-section-head">
          <div>
            <p className="eyebrow">Collections</p>
            <h2>Choose collection</h2>
          </div>
          <span className="section-count">
            {visibleCollections.length} shown
          </span>
        </div>
        <div className="collection-grid">
          {visibleCollections.map((collection) => (
            <CollectionCard
              key={collection.slug}
              collection={collection}
              colorIndex={collections.indexOf(collection)}
              topics={topics.filter((topic) =>
                topic.path.startsWith(`${collection.slug}/`),
              )}
            />
          ))}
        </div>
      </section>

      {visibleCollections.length === 0 && (
        <div className="empty-state">
          <strong>No collections matched.</strong>
          <span>
            Try collection name, topic name, section name, or source domain.
          </span>
        </div>
      )}
    </>
  );
}
