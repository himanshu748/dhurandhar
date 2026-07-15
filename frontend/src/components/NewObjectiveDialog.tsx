import { LoaderCircle, X } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { createObjective } from "../api";

export function NewObjectiveDialog({
  open,
  operatorToken,
  onClose,
  onCreated,
}: {
  open: boolean;
  operatorToken: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && !dialog.current?.open) {
      if (typeof dialog.current?.showModal === "function") dialog.current.showModal();
      else dialog.current?.setAttribute("open", "");
    }
    if (!open && dialog.current?.open) dialog.current.close();
  }, [open]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setSubmitting(true);
    setError(null);
    try {
      await createObjective({
        title: String(data.get("title")),
        description: String(data.get("description")),
        acceptanceCriteria: String(data.get("acceptanceCriteria"))
          .split("\n")
          .map((criterion) => criterion.trim())
          .filter(Boolean),
        priority: String(data.get("priority")) === "urgent" ? "urgent" : "standard",
      }, operatorToken);
      onCreated();
      onClose();
      event.currentTarget.reset();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to create objective");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <dialog ref={dialog} className="objective-dialog" onClose={onClose} onCancel={onClose}>
      <form method="dialog" onSubmit={submit}>
        <div className="dialog-heading">
          <div><h2>New objective</h2><p>Define the outcome. The kernel will create an auditable run.</p></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close objective dialog"><X size={18} /></button>
        </div>
        <label>
          Objective
          <input name="title" required minLength={5} defaultValue="Harden Change Replay ordering" />
        </label>
        <label>
          Context
          <textarea name="description" required rows={3} defaultValue="Harden replay ordering without weakening the immutable event journal." />
        </label>
        <label>
          Acceptance criteria <small className="field-hint">one per line</small>
          <textarea name="acceptanceCriteria" required rows={4} defaultValue={"Replay events stay deterministic when timestamps collide.\nA regression test covers the collision.\nThe hash chain remains valid."} />
        </label>
        <fieldset>
          <legend>Priority</legend>
          <label className="radio-row"><input type="radio" name="priority" value="standard" defaultChecked /><span><strong>Standard</strong><small>Normal delivery and recovery gates.</small></span></label>
          <label className="radio-row"><input type="radio" name="priority" value="urgent" /><span><strong>Urgent</strong><small>Recorded as urgent; safety gates still apply.</small></span></label>
        </fieldset>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="dialog-actions">
          <button className="secondary-action" type="button" onClick={onClose}>Cancel</button>
          <button className="primary-action simple" type="submit" disabled={submitting}>
            {submitting && <LoaderCircle className="spin" size={15} />}
            Start objective
          </button>
        </div>
      </form>
    </dialog>
  );
}
