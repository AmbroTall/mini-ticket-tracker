import { PRIORITIES, STATUSES } from "../api.js";

const formatDate = (iso) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export default function TicketList({ tickets, filter, pendingId, onUpdate }) {
  if (tickets.length === 0) {
    const label = STATUSES.find((s) => s.value === filter)?.label.toLowerCase();
    return (
      <p className="empty">
        {label ? `No ${label} tickets.` : "No tickets yet. Create the first one using the form."}
      </p>
    );
  }

  return (
    <ul className="tickets">
      {tickets.map((ticket) => (
        <li key={ticket.id} className={`ticket priority-${ticket.priority}`}>
          <div className="ticket-body">
            <h3>{ticket.title}</h3>
            {ticket.description && <p className="description">{ticket.description}</p>}
            <p className="meta">
              <span>#{ticket.id}</span> <span>Created {formatDate(ticket.created_at)}</span>
            </p>
          </div>

          <div className="ticket-controls">
            <select
              className="status-select"
              data-status={ticket.status}
              aria-label={`Status of ticket ${ticket.id}`}
              value={ticket.status}
              disabled={pendingId === ticket.id}
              onChange={(e) => onUpdate(ticket.id, { status: e.target.value })}
            >
              {STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
            <select
              className="priority-select"
              aria-label={`Priority of ticket ${ticket.id}`}
              value={ticket.priority}
              disabled={pendingId === ticket.id}
              onChange={(e) => onUpdate(ticket.id, { priority: e.target.value })}
            >
              {PRIORITIES.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label} priority
                </option>
              ))}
            </select>
          </div>
        </li>
      ))}
    </ul>
  );
}
