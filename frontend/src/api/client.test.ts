import { describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockFetch } from '../test/utils'
import { ApiError, errorMessage, request } from './client'

describe('request', () => {
  it('calls the relative /api base with JSON headers and returns the body', async () => {
    const fetch = mockFetch(() => jsonResponse({ ok: true }))

    await expect(request('/expenses?page=1')).resolves.toEqual({ ok: true })

    const [url, init] = fetch.mock.calls[0]
    expect(url).toBe('/api/expenses?page=1')
    expect(init?.headers).toMatchObject({ 'Content-Type': 'application/json' })
  })

  it('throws ApiError with the server {error} message and status', async () => {
    mockFetch(() => jsonResponse({ error: 'title is required' }, 400))

    const error = await request('/expenses').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ message: 'title is required', status: 400 })
  })

  it('falls back to a generic message when the error body is not {error}', async () => {
    mockFetch(() => ({ ok: false, status: 502, json: async () => Promise.reject(new Error("not json")) }) as unknown as Response)

    await expect(request('/expenses')).rejects.toMatchObject({ message: 'Request failed (502)', status: 502 })
  })

  it('returns undefined for 204 without reading the body', async () => {
    const json = vi.fn()
    mockFetch(() => ({ ok: true, status: 204, json }) as unknown as Response)

    await expect(request('/expenses/1', { method: 'DELETE' })).resolves.toBeUndefined()
    expect(json).not.toHaveBeenCalled()
  })

  it('maps network failures to ApiError with status 0', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(request('/expenses')).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: 'Could not reach the server. Check your connection and try again.',
    })
  })
})

describe('errorMessage', () => {
  it('uses Error messages and falls back for unknown values', () => {
    expect(errorMessage(new Error('boom'))).toBe('boom')
    expect(errorMessage('nope')).toBe('Something went wrong')
  })
})
