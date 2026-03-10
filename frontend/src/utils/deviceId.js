const STORAGE_KEY = 'classqr_device_id'

function randomId() {
  if (typeof globalThis.crypto !== 'undefined' && typeof globalThis.crypto.randomUUID === 'function') {
    return globalThis.crypto.randomUUID()
  }
  return `dev-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 14)}`
}

/** Стабильный id браузера; не очищается при «Выйти» — чтобы один телефон = один аккаунт на пару. */
export function getDeviceId() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return randomId()
  }
  let id = localStorage.getItem(STORAGE_KEY)
  if (!id || id.length < 8) {
    id = randomId()
    localStorage.setItem(STORAGE_KEY, id)
  }
  return id
}
