import { useEffect, useState } from "react";
import { STATUSES, createTicket, getStats, listTickets, updateTicket } from "./api.js";
import TicketForm from "./components/TicketForm.jsx";
import TicketList from "./components/TicketList.jsx";

const PAGE_SIZE = 10;

export default function App() {
  const [filter, setFilter] = useState(""); // "" means all statuses
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ count: 0, results: [] });
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pendingId, setPendingId] = useState(null);
  const [version, setVersion] = useState(0); // bump to refetch after a mutation

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    listTickets({ status: filter, page, limit: PAGE_SIZE })
      .then((result) => {
        if (ignore) return;
        setData(result);
        setError("");
      })
      .catch((err) => {
        if (ignore) return;
        // The current page can vanish when a status change shrinks the filtered list.
        if (err.status === 404 && page > 1) setPage(1);
        else setError(err.message);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [filter, page, version]);

  useEffect(() => {
    let ignore = false;
    getStats()
      .then((result) => !ignore && setStats(result))
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, [version]);

  const refresh = () => setVersion((v) => v + 1);

  async function handleCreate(payload) {
    await createTicket(payload); // errors surface in the form
    setFilter("");
    setPage(1);
    refresh();
  }

  async function handleUpdate(id, changes) {
    setPendingId(id);
    try {
      await updateTicket(id, changes);
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setPendingId(null);
    }
  }

  const changeFilter = (value) => {
    setFilter(value);
    setPage(1);
  };

  const total = stats ? Object.values(stats).reduce((a, b) => a + b, 0) : null;
  const pages = Math.max(1, Math.ceil(data.count / PAGE_SIZE));

  return (
    <div className="shell">
      <header className="masthead">
        <h1>Mini Ticket Tracker</h1>
      </header>

      <nav className="counts" aria-label="Filter tickets by status">
        <button className="count" aria-pressed={filter === ""} onClick={() => changeFilter("")}>
          <span className="count-number">{total ?? "–"}</span>
          <span className="count-label">All</span>
        </button>
        {STATUSES.map((s) => (
          <button
            key={s.value}
            className="count"
            data-status={s.value}
            aria-pressed={filter === s.value}
            onClick={() => changeFilter(s.value)}
          >
            <span className="count-number">{stats ? stats[s.value] : "–"}</span>
            <span className="count-label">{s.label}</span>
          </button>
        ))}
      </nav>

      <main className="layout">
        <TicketForm onCreate={handleCreate} />

        <section className="queue" aria-busy={loading}>
          {error && (
            <p className="error banner" role="alert">
              {error}
            </p>
          )}
          {loading && data.results.length === 0 && !error ? (
            <p className="empty">Loading tickets…</p>
          ) : (
            <TicketList tickets={data.results} filter={filter} pendingId={pendingId} onUpdate={handleUpdate} />
          )}

          {pages > 1 && (
            <div className="pager">
              <button disabled={page <= 1 || loading} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span>
                Page {page} of {pages}
              </span>
              <button disabled={page >= pages || loading} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
