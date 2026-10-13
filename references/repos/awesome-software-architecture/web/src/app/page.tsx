import { HomeAtlas } from "@/components/home-atlas";
import { ThemeToggle } from "@/components/theme-toggle";
import { getCatalog } from "@/lib/content";
import Link from "next/link";

export default function Home() {
  const catalog = getCatalog();

  return (
    <main>
      <a className="skip-link" href="#collection">
        Skip to collection
      </a>
      <nav className="site-nav" aria-label="Main navigation">
        <Link className="brand" href="/">
          <span className="brand-mark">A</span>
          <span>
            Awesome
            <br />
            <em>Architecture</em>
          </span>
        </Link>
        <div className="nav-links">
          <a className="nav-current" href="#collections">
            Collections
          </a>
          <a href="#topics">Topics</a>
          <a
            href="https://github.com/mehdihadeli/awesome-software-architecture"
            target="_blank"
            rel="noreferrer"
          >
            Source
          </a>
        </div>
        <a
          className="github-link"
          href="https://github.com/mehdihadeli/awesome-software-architecture"
          target="_blank"
          rel="noreferrer"
        >
          View on GitHub <span aria-hidden="true">↗</span>
        </a>
        <ThemeToggle />
      </nav>
      <div className="page-shell" id="collection">
        <HomeAtlas {...catalog} />
      </div>
      <footer className="site-footer">
        <span>Awesome Architecture</span>
        <span>Made for curious builders.</span>
        <span>Open source collection ↗</span>
      </footer>
    </main>
  );
}
