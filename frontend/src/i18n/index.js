import { computed, inject, ref } from 'vue'
import messages from './messages'

const I18N_KEY = Symbol('mirofish-i18n')
const RTL_LOCALES = new Set(['ar'])
const LOCALE_STORAGE_KEY = 'mirofish.locale'

const normalizeLocale = (candidate) => {
  if (!candidate || typeof candidate !== 'string') return null
  const base = candidate.toLowerCase().split('-')[0]
  return messages[base] ? base : null
}

const detectInitialLocale = () => {
  if (typeof window === 'undefined') {
    return 'ar'
  }

  const stored = normalizeLocale(window.localStorage.getItem(LOCALE_STORAGE_KEY))
  if (stored) return stored

  const queryLocale = normalizeLocale(new URLSearchParams(window.location.search).get('lang'))
  if (queryLocale) return queryLocale

  return 'ar'
}

const currentLocale = ref(detectInitialLocale())

const getMessageValue = (locale, path) => {
  const segments = path.split('.')
  let cursor = messages[locale]

  for (const segment of segments) {
    if (cursor == null || typeof cursor !== 'object' || !(segment in cursor)) {
      return undefined
    }
    cursor = cursor[segment]
  }

  return cursor
}

const interpolate = (template, params = {}) => {
  if (typeof template !== 'string') return template
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = params[key]
    return value == null ? `{${key}}` : String(value)
  })
}

const applyDocumentLocale = (locale) => {
  if (typeof document === 'undefined') return

  const lang = locale === 'zh' ? 'zh-CN' : locale
  const dir = RTL_LOCALES.has(locale) ? 'rtl' : 'ltr'

  document.documentElement.lang = lang
  document.documentElement.dir = dir
  document.body?.setAttribute('dir', dir)
}

applyDocumentLocale(currentLocale.value)

export const availableLocales = [
  { code: 'ar', label: messages.ar.language.names.ar },
  { code: 'en', label: messages.en.language.names.en },
  { code: 'zh', label: messages.zh.language.names.zh }
]

export const getCurrentLocale = () => currentLocale.value

export const setLocale = (locale) => {
  const normalized = normalizeLocale(locale)
  if (!normalized) return

  currentLocale.value = normalized
  applyDocumentLocale(normalized)

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, normalized)
  }
}

export const t = (path, params = {}) => {
  const localizedValue = getMessageValue(currentLocale.value, path)
  const fallbackValue = getMessageValue('en', path)
  const finalValue = localizedValue ?? fallbackValue ?? path

  return interpolate(finalValue, params)
}

export const createMiroI18n = () => ({
  install(app) {
    const api = {
      locale: currentLocale,
      setLocale,
      t,
      availableLocales,
      isRtl: computed(() => RTL_LOCALES.has(currentLocale.value))
    }

    app.provide(I18N_KEY, api)
    app.config.globalProperties.$t = t
  }
})

export const useI18n = () => {
  const injected = inject(I18N_KEY, null)

  if (injected) {
    return injected
  }

  return {
    locale: currentLocale,
    setLocale,
    t,
    availableLocales,
    isRtl: computed(() => RTL_LOCALES.has(currentLocale.value))
  }
}

export default {
  createMiroI18n,
  useI18n,
  t,
  setLocale,
  getCurrentLocale,
  availableLocales
}
