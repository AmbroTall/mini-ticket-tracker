import { useState } from "react";
import { PRIORITIES } from "../api.js";

const EMPTY = { title: "", description: "", priority: "medium" };

export default function TicketForm({ onCreate }) {
  const [values, setValues] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const set = (field) => (event) => setValues({ ...values, [field]: event.target.value });

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await onCreate({ ...values, title: values.title.trim() });
      setValues(EMPTY);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel form" onSubmit={handleSubmit}>
      <h2>New ticket</h2>

      <label>
        Title
        <input value={values.title} onChange={set("title")} maxLength={200} required />
      </label>

      <label>
        Description
        <textarea value={values.description} onChange={set("description")} rows={4} />
      </label>

      <label>
        Priority
        <select value={values.priority} onChange={set("priority")}>
          {PRIORITIES.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </label>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="primary" disabled={submitting || !values.title.trim()}>
        {submitting ? "Creating…" : "Create ticket"}
      </button>
    </form>
  );
}
