"use client";

import { useMemo, useState } from "react";
import { TypeIcon } from "@/components/type-icon";
import type { Resource, Topic } from "@/lib/content";

const categories = ["All", "AI Engineering", "Microservices"];
const resourceTypes = [
  "All types",
  "Article",
  "Video",
  "Course",
  "Book",
  "Library",
  "Sample",
  "Tool",
  "Resource",
];

function Stat({
  value,
  label,
  tone,
}: {
  value: string;
  label: string;
  tone: string;
}) {
  return (
    <div className={`stat stat-${tone}`}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function TopicCard({ topic }: { topic: Topic }) {
  return (
    <article className="topic-card">
      <div className="topic-card-top">
        <span className="topic-mark">
          {topic.category === "AI Engineering" ? "✦" : "◈"}
        </span>
        <span className="topic-label">{topic.category}</span>
      </div>
      <h3>{topic.title}</h3>
      <p>{topic.description}</p>
      <div className="topic-card-footer">
        <span>{topic.resourceCount} resources</span>
        <a href={`/topics/${topic.slug}`}>
          Explore topic <span aria-hidden="true">↗</span>
        </a>
      </div>
    </article>
  );
}

function ResourceCard({ resource }: { resource: Resource }) {
  return (
    <article
      className={`resource-card resource-${resource.type.toLowerCase()}`}
    >
      <div className="resource-card-top">
        <span className="resource-icon" aria-hidden="true">
          <TypeIcon type={resource.type} />
        </span>
        <span className="resource-type">{resource.type}</span>
      </div>
      <h3>{resource.title}</h3>
      <p>{resource.description}</p>
      <div className="resource-meta">
        <span>{resource.topic}</span>
        <span>{resource.domain}</span>
      </div>
      <a
        className="resource-link"
        href={resource.url}
        target="_blank"
        rel="noreferrer"
      >
        Open resource <span aria-hidden="true">↗</span>
      </a>
    </article>
  );
}

export function Catalog({
  topics,
  resources,
}: {
  topics: Topic[];
  resources: Resource[];
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [type, setType] = useState("All types");
  const [view, setView] = useState<"resources" | "topics">("resources");
  const [sort, setSort] = useState("relevance");

  const filteredResources = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return resources
      .filter(
        (resource) =>
          category === "All" ||
          resource.topicSlug.startsWith(
            category === "AI Engineering" ? "ai-" : "microservices-",
          ),
      )
      .filter((resource) => type === "All types" || resource.type === type)
      .filter(
        (resource) =>
          !normalizedQuery ||
          `${resource.title} ${resource.description} ${resource.topic} ${resource.domain}`
            .toLowerCase()
            .includes(normalizedQuery),
      )
      .sort((first, second) =>
        sort === "title"
          ? first.title.localeCompare(second.title)
          : first.topic.localeCompare(second.topic),
      );
  }, [category, query, resources, sort, type]);

  const filteredTopics = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return topics.filter(
      (topic) =>
        (category === "All" || topic.category === category) &&
        (!normalizedQuery ||
          `${topic.title} ${topic.description} ${topic.category}`
            .toLowerCase()
            .includes(normalizedQuery)),
    );
  }, [category, query, topics]);

  return (
    <>
      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">A field guide for better systems</p>
          <h1>Find the architecture idea you need next.</h1>
          <p className="hero-lede">
            A curated atlas of patterns, systems, AI engineering, and practical
            resources. Search by problem, browse by domain, or follow a learning
            path.
          </p>
          <label className="search-box">
            <span aria-hidden="true">⌕</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search topics, articles, tools, and resources..."
            />
            <kbd>/</kbd>
          </label>
        </div>
        <div className="hero-note">
          <span className="hero-note-number">01</span>
          <p>
            Start with a topic. Follow the connections. Leave with a decision
            you can explain.
          </p>
          <div className="hero-lines" aria-hidden="true">
            <i />
            <i />
            <i />
          </div>
        </div>
      </section>

      <section className="stats-grid" aria-label="Catalog statistics">
        <Stat value={`${topics.length}`} label="Topic pages" tone="blue" />
        <Stat
          value={`${resources.length}`}
          label="Curated resources"
          tone="orange"
        />
        <Stat value="12" label="Architecture domains" tone="green" />
        <Stat value="Open" label="Community collection" tone="pink" />
      </section>

      <section className="control-panel" aria-label="Catalog filters">
        <div className="control-heading">
          <span>Explore the collection</span>
          <small>
            {view === "resources"
              ? filteredResources.length
              : filteredTopics.length}{" "}
            results
          </small>
        </div>
        <div className="filter-row">
          {categories.map((item) => (
            <button
              className={
                category === item ? "filter-chip active" : "filter-chip"
              }
              key={item}
              onClick={() => setCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <div className="control-bottom">
          <div className="view-switch" role="tablist" aria-label="Catalog view">
            <button
              className={view === "resources" ? "view-tab active" : "view-tab"}
              onClick={() => setView("resources")}
            >
              Resources
            </button>
            <button
              className={view === "topics" ? "view-tab active" : "view-tab"}
              onClick={() => setView("topics")}
            >
              Topics
            </button>
          </div>
          {view === "resources" && (
            <select
              value={type}
              onChange={(event) => setType(event.target.value)}
              aria-label="Filter by resource type"
            >
              {resourceTypes.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          )}
          <select
            value={sort}
            onChange={(event) => setSort(event.target.value)}
            aria-label="Sort results"
          >
            <option value="relevance">Sort: Relevance</option>
            <option value="title">Sort: Title</option>
          </select>
        </div>
      </section>

      <section className="results-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Browse the atlas</p>
            <h2>
              {view === "resources" ? "Curated resources" : "Topic pages"}
            </h2>
          </div>
          <span className="result-count">
            {view === "resources"
              ? filteredResources.length
              : filteredTopics.length}{" "}
            shown
          </span>
        </div>
        {view === "resources" ? (
          <div className="resource-grid">
            {filteredResources.slice(0, 48).map((resource) => (
              <ResourceCard key={resource.id} resource={resource} />
            ))}
          </div>
        ) : (
          <div className="topic-grid">
            {filteredTopics.map((topic) => (
              <TopicCard key={topic.slug} topic={topic} />
            ))}
          </div>
        )}
        {(view === "resources"
          ? filteredResources.length
          : filteredTopics.length) === 0 && (
          <div className="empty-state">
            <strong>No matches yet.</strong>
            <span>Try a broader phrase or clear one of the filters.</span>
          </div>
        )}
      </section>
    </>
  );
}
