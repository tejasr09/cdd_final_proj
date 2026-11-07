function App() {
  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Ripple Effect home">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>Ripple Effect</span>
        </a>
        <span className="phase-label">Project foundation</span>
      </header>

      <section className="welcome" aria-labelledby="welcome-title">
        <p className="eyebrow">
          EVENT → DEPENDENCIES → CONSEQUENCES → DECISIONS
        </p>
        <h1 id="welcome-title">See what a change may affect.</h1>
        <p className="intro">
          Model relationships, explore possible ripple effects, and review the
          assumptions behind each estimate.
        </p>
        <aside className="notice" role="note">
          <strong>Estimates, not probabilities.</strong> Results will depend on
          the relationships and assumptions people provide.
        </aside>
      </section>

      <section className="status-card" aria-labelledby="status-title">
        <div className="status-icon" aria-hidden="true">
          1
        </div>
        <div>
          <h2 id="status-title">Foundation is in place</h2>
          <p>
            The web shell and API health checks are ready. Event management,
            dependency modeling, and analysis are planned for upcoming phases.
          </p>
        </div>
      </section>

      <footer className="page-footer">
        <span>Ripple Effect</span>
        <span>Decision support for modeled dependencies</span>
      </footer>
    </main>
  );
}

export default App;
