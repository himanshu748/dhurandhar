import { Check, KeyRound, LockKeyhole, X } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";

export function OperatorAccessDialog({
  open,
  tokenLoaded,
  onClose,
  onLoadToken,
  onForgetToken,
}: {
  open: boolean;
  tokenLoaded: boolean;
  onClose: () => void;
  onLoadToken: (token: string) => void;
  onForgetToken: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (open && !dialog.current?.open) {
      if (typeof dialog.current?.showModal === "function") dialog.current.showModal();
      else dialog.current?.setAttribute("open", "");
    }
    if (!open && dialog.current?.open) {
      if (typeof dialog.current.close === "function") dialog.current.close();
      else dialog.current.removeAttribute("open");
    }
  }, [open]);

  useEffect(() => {
    if (!open) setDraft("");
  }, [open]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const token = draft.trim();
    if (token.length < 16) return;
    setDraft("");
    onLoadToken(token);
  };

  const forget = () => {
    setDraft("");
    onForgetToken();
  };

  return (
    <dialog ref={dialog} className="objective-dialog operator-dialog" onClose={onClose} onCancel={onClose}>
      <form onSubmit={submit}>
        <div className="dialog-heading">
          <div>
            <h2>Operator access</h2>
            <p>Load a server-configured token for this browser tab only.</p>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close operator access dialog"><X size={18} /></button>
        </div>

        {tokenLoaded ? (
          <>
            <div className="operator-loaded" role="status">
              <Check size={16} aria-hidden="true" />
              <span><strong>Token loaded in memory</strong><small>It is attached only to mutation request headers and is forgotten on reload.</small></span>
            </div>
            <p className="operator-boundary"><LockKeyhole size={14} aria-hidden="true" />The token is never written to browser storage, bundled into the app, or placed in event payloads.</p>
            <div className="dialog-actions">
              <button className="secondary-action danger-action" type="button" onClick={forget}>Forget token</button>
              <button className="primary-action simple" type="button" onClick={onClose}>Done</button>
            </div>
          </>
        ) : (
          <>
            <label>
              Operator token <small className="field-hint">kept in memory only</small>
              <span className="operator-input-wrap">
                <KeyRound size={15} aria-hidden="true" />
                <input
                  name="operatorToken"
                  type="password"
                  value={draft}
                  onChange={(event) => setDraft(event.currentTarget.value)}
                  required
                  minLength={16}
                  maxLength={256}
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  aria-describedby="operator-token-help"
                  autoFocus
                />
              </span>
            </label>
            <p id="operator-token-help" className="operator-boundary"><LockKeyhole size={14} aria-hidden="true" />Without a valid token, this control plane stays read-only. The server checks the token when an action is submitted.</p>
            <div className="dialog-actions">
              <button className="secondary-action" type="button" onClick={onClose}>Cancel</button>
              <button className="primary-action simple" type="submit" disabled={draft.trim().length < 16}>
                <KeyRound size={15} />
                Load token
              </button>
            </div>
          </>
        )}
      </form>
    </dialog>
  );
}
