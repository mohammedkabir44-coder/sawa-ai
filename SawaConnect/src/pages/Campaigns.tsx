import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { campaignsApi, type CampaignOut } from '../lib/api'

type Channel = 'whatsapp' | 'sms' | 'both'
type AudienceKind = 'all' | 'tag'

const CHANNEL_LABELS: Record<Channel, string> = {
  whatsapp: 'WhatsApp',
  sms: 'SMS',
  both: 'Both',
}

function statusStyle(status: string) {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'running':
      return 'bg-blue-100 text-blue-700'
    case 'draft':
      return 'bg-amber-100 text-amber-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function formatDate(value: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

interface Toast {
  kind: 'success' | 'error'
  message: string
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<CampaignOut[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [executingId, setExecutingId] = useState<number | null>(null)
  const [toast, setToast] = useState<Toast | null>(null)

  const showToast = useCallback((kind: Toast['kind'], message: string) => {
    setToast({ kind, message })
    window.setTimeout(() => setToast(null), 4000)
  }, [])

  const loadCampaigns = useCallback(async () => {
    setLoading(true)
    try {
      const data = await campaignsApi.list()
      setCampaigns(data.items)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    loadCampaigns()
  }, [loadCampaigns])

  async function handleExecute(id: number, name: string) {
    setExecutingId(id)
    try {
      const result = await campaignsApi.execute(id)
      showToast(
        'success',
        `Campaign "${name}" sent: ${result.sent} delivered, ${result.failed} failed`,
      )
      await loadCampaigns()
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Campaign send failed')
    } finally {
      setExecutingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Campaigns</h2>
          <p className="mt-1 text-sm text-gray-500">
            Send promotions to your customers over WhatsApp and SMS.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Create Campaign
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
                Channel
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Status
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Created
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-400">
                  Loading campaigns…
                </td>
              </tr>
            ) : campaigns.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-400">
                  No campaigns yet. Click &ldquo;Create Campaign&rdquo; to get started.
                </td>
              </tr>
            ) : (
              campaigns.map((c) => {
                const channelKey = (
                  Object.prototype.hasOwnProperty.call(CHANNEL_LABELS, c.channel)
                    ? c.channel
                    : 'whatsapp'
                ) as Channel
                const canSend = c.status === 'draft' || c.status === 'failed' || c.status === 'scheduled'
                return (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {c.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {CHANNEL_LABELS[channelKey]}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyle(c.status)}`}
                      >
                        {c.status.charAt(0).toUpperCase() + c.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {formatDate(c.created_at)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        type="button"
                        disabled={!canSend || executingId === c.id}
                        onClick={() => handleExecute(c.id, c.name)}
                        className="rounded-md bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {executingId === c.id ? 'Sending…' : 'Send Now'}
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <CreateCampaignModal
          onClose={() => setShowModal(false)}
          onCreated={(name) => {
            setShowModal(false)
            showToast('success', `Campaign "${name}" created`)
            loadCampaigns()
          }}
          onError={(message) => showToast('error', message)}
        />
      )}
    </div>
  )
}

interface CreateCampaignModalProps {
  onClose: () => void
  onCreated: (name: string) => void
  onError: (message: string) => void
}

function CreateCampaignModal({ onClose, onCreated, onError }: CreateCampaignModalProps) {
  const [name, setName] = useState('')
  const [channel, setChannel] = useState<Channel>('whatsapp')
  const [message, setMessage] = useState('')
  const [audienceKind, setAudienceKind] = useState<AudienceKind>('all')
  const [tag, setTag] = useState('VIP')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const audience: Record<string, unknown> =
        audienceKind === 'all'
          ? { all: true }
          : { tags: tag.split(',').map((t) => t.trim()).filter(Boolean) }
      const created = await campaignsApi.create({
        name,
        channel,
        audience,
        message,
        language: 'en',
      })
      onCreated(created.name)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Campaign creation failed')
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass =
    'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500'

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-gray-900/50 p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-lg rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Create Campaign</h3>
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
            <label htmlFor="campaign-name" className="block text-sm font-medium text-gray-700">
              Campaign Name
            </label>
            <input
              id="campaign-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="E.g. Ramadan Sale 2026"
              className={inputClass}
            />
          </div>

          <div>
            <label htmlFor="campaign-channel" className="block text-sm font-medium text-gray-700">
              Channel
            </label>
            <select
              id="campaign-channel"
              value={channel}
              onChange={(e) => setChannel(e.target.value as Channel)}
              className={inputClass}
            >
              <option value="whatsapp">WhatsApp</option>
              <option value="sms">SMS</option>
              <option value="both">Both</option>
            </select>
          </div>

          <div>
            <label htmlFor="campaign-message" className="block text-sm font-medium text-gray-700">
              Message
            </label>
            <textarea
              id="campaign-message"
              required
              rows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Great news! 20% off everything this weekend…"
              className={inputClass}
            />
          </div>

          <div>
            <label htmlFor="campaign-audience" className="block text-sm font-medium text-gray-700">
              Audience Filter
            </label>
            <select
              id="campaign-audience"
              value={audienceKind}
              onChange={(e) => setAudienceKind(e.target.value as AudienceKind)}
              className={inputClass}
            >
              <option value="all">All Customers</option>
              <option value="tag">Tag: VIP</option>
            </select>
            {audienceKind === 'tag' && (
              <input
                type="text"
                value={tag}
                onChange={(e) => setTag(e.target.value)}
                placeholder="Comma-separated tags, e.g. VIP, repeat-buyer"
                className={inputClass}
              />
            )}
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
              {submitting ? 'Creating…' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}