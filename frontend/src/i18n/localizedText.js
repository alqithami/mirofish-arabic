import { useI18n } from './index'

const interpolate = (template, params = {}) => {
  if (typeof template !== 'string') return template
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = params[key]
    return value == null ? `{${key}}` : String(value)
  })
}

const resolveLocalizedValue = (entry, locale) => {
  if (entry == null) return ''
  if (typeof entry === 'string') return entry
  if (Array.isArray(entry)) return entry
  if (typeof entry !== 'object') return entry

  return (
    entry[locale]
    ?? entry.en
    ?? entry.ar
    ?? entry.zh
    ?? Object.values(entry)[0]
    ?? ''
  )
}

export const useLocalizedText = () => {
  const { locale, isRtl } = useI18n()

  const pick = (entry, params = {}) => {
    const value = resolveLocalizedValue(entry, locale.value)
    if (Array.isArray(value)) {
      return value.map(item => pick(item, params))
    }
    return interpolate(value, params)
  }

  return {
    locale,
    isRtl,
    pick
  }
}

export default useLocalizedText
