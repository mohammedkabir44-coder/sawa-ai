import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  automationsApi,
  triggerLabel,
  type AutomationOut,
  type AutomationStepCreate,
} from '../lib/api'

interface Toast {
  kind: 'success' | 'error'
  message: string
}

type StepKind = 'send_whatsapp' | 'send_sms' | 'wait'

const STEP_LABELS: Record<StepKind, string> = {
  send_whatsapp: 'Send WhatsApp',
  send_sms: 'Send SMS',
  wait: 'Wait',
}

function stepToPayload(step: StepDraft): AutomationStepCreate {
  if (step.kind === 'wait') {
    return {
      step_type: 'delay',
      action_type: 'wait_delay',
      config: { hours: Number(step.hours) || 0 },
      order_index: step.order,
    }
  }
  return {
    step_type: 'action',
    action_type: step.kind,
    config: {},
    order_index: step.order,
  }
}

interface StepDraft {
  key: number
  kind: StepKind
  hours: string
  order: number
}

let stepKeyCounter = 0

export default function Automations() {
  const [automations, setAutomations] = useState<AutomationOut[]>([])
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<number | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)

  const showToast = useCallback((kind: Toast['kind'], message: string) => {
    setToast({ kind, message })
    window.setTimeout(() => setToast(null), 4000)
  }, [])

  const loadAutomations = useCallback(async () => {
    setLoading(true)
    try {
      const data = await automationsApi.list()
      setAutomations(data.items)
    } catch (err) {
      showToast(
        'error',
        err instanceof Error ? err.message : 'Failed to load automations',
      )
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadAutomations()
  }, [loadAutomations])

async function handleToggle(a: AutomationOut) {
    setTogglingId(a.id)
    try {
      await automationsApi.update(a.id, { is_active: !a.is_active })
      showToast(
        'success',
        `"${a.name}" is now ${a.is_active ? 'paused' : 'active'}`,
      )
      await loadAutomations()
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Toggle failed')
    } finally {
      setTogglingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Automations</h2>
          <p className="mt-1 text-sm text-gray-500">
            Build Zapier-style workflows that react to your business events.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Create Automation
        </button>
      </div>

      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 rounded-lg px-4 py-3 text-sm font-medium shadow-lg ${
            toast.kind === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}
          role="status"
        >
          {toast.message}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Name
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Trigger
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Status
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Active
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-sm text-gray-400">
                  Loading automations…
                </td>
              </tr>
            ) : automations.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-sm text-gray-400">
                  No automations yet. Click &ldquo;Create Automation&rdquo; to build one.
                </td>
              </tr>
            ) : (
              automations.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {a.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {triggerLabel(a.trigger_type)}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        a.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {a.is_active ? 'Active' : 'Paused'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={a.is_active}
                      disabled={togglingId === a.id}
                      onClick={() => handleToggle(a)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 ${
                        a.is_active ? 'bg-indigo-600' : 'bg-gray-300'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                          a.is_active ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <CreateAutomationModal
          onClose={() => setShowModal(false)}
          onCreated={(name) => {
            setShowModal(false)
            showToast('success', `Automation "${name}" created`)
            loadAutomations()
          }}
          onError={(message) => showToast('error', message)}
        />
      )}
    </div>
  )
}

interface CreateAutomationModalProps {
  onClose: () => void
  onCreated: (name: string) => void
  onError: (message: string) => void
}

type AutomationCreateTrigger =
  | 'whatsapp_message_received'
  | 'new_lead_created'
  | 'scheduled_time'

function CreateAutomationModal({
  onClose,
  onCreated,
  onError,
}: CreateAutomationModalProps) {
  const [name, setName] = useState('')
  const [trigger, setTrigger] = useState('whatsapp_message_received')
  const [steps, setSteps] = useState<StepDraft[]>([])
  const [submitting, setSubmitting] = useState(false)

  function addStep(kind: StepKind) {
    stepKeyCounter += 1
    setSteps((prev) => [
      ...prev,
      { key: stepKeyCounter, kind, hours: '1', order: prev.length },
    ])
  }

  function removeStep(key: number) {
    setSteps((prev) =>
      prev.filter((s) => s.key !== key).map((s, i) => ({ ...s, order: i })),
    )
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const created = await automationsApi.create({
        name,
        is_active: true,
        trigger_type: trigger as AutomationCreateTrigger,
        steps: steps.map(stepToPayload),
      })
      onCreated(created.name)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Automation creation failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-gray-900/50 p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Create Automation</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="automation-name" className="block text-sm font-medium text-gray-700">
              Name
            </label>
            <input
              id="automation-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="E.g. Welcome new customers"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label htmlFor="automation-trigger" className="block text-sm font-medium text-gray-700">
              Trigger
            </label>
            <select
              id="automation-trigger"
              value={trigger}
              onChange={(e) => setTrigger(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="whatsapp_message_received">WhatsApp message received</option>
              <option value="new_lead_created">New lead created</option>
              <option value="scheduled_time">Scheduled time</option>
            </select>
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-700">Steps</span>
            <div className="mt-2 space-y-2">
              {steps.length === 0 && (
                <p className="text-sm text-gray-400">No steps yet - add an action below.</p>
              )}
              {steps.map((s, i) => (
                <StepRow
                  key={s.key}
                  index={i}
                  draft={s}
                  onHoursChange={(hours) =>
                    setSteps((prev) =>
                      prev.map((x) => (x.key === s.key ? { ...x, hours } : x)),
                    )
                  }
                  onRemove={() => removeStep(s.key)}
                />
              ))}
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {(Object.keys(STEP_LABELS) as StepKind[]).map((kind) => (
                <button
                  key={kind}
                  type="button"
                  onClick={() => addStep(kind)}
                  className="rounded-md bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 transition-colors hover:bg-indigo-100"
                >
                  + Add Step: {STEP_LABELS[kind]}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:opacity-60"
            >
              {submitting ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

interface StepRowProps {
  index: number
  draft: StepDraft
  onHoursChange: (hours: string) => void
  onRemove: () => void
}

function StepRow({ index, draft, onHoursChange, onRemove }: StepRowProps) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
      <span className="text-xs font-semibold text-gray-400">{index + 1}.</span>
      <span className="flex-1 text-sm text-gray-700">
        {STEP_LABELS[draft.kind]}
        {draft.kind === 'wait' && (
          <>
            <input
              type="number"
              min="0"
              step="any"
              value={draft.hours}
              onChange={(e) => onHoursChange(e.target.value)}
              className="ml-2 w-16 rounded border border-gray-300 px-1 py-0.5 text-sm"
            />
            <span className="ml-1 text-gray-500">hours</span>
          </>
        )}
      </span>
      <button
        type="button"
        onClick={onRemove}
        className="text-sm font-medium text-red-600 hover:text-red-800"
        aria-label={`Remove step ${index + 1}`}
      >
        Remove
      </button>
    </div>
  )
}