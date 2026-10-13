import { notFound } from "next/navigation";
import { TopicExplorer } from "@/components/topic-explorer";
import { getCatalog } from "@/lib/content";

type TopicPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return getCatalog().topics.map((topic) => ({ slug: topic.slug }));
}

export default async function TopicPage({ params }: TopicPageProps) {
  const { slug } = await params;
  const catalog = getCatalog();
  const topic = catalog.topics.find((item) => item.slug === slug);

  if (!topic) notFound();

  return (
    <TopicExplorer
      topic={topic}
      resources={catalog.resources.filter(
        (resource) => resource.topicSlug === topic.slug,
      )}
    />
  );
}
