import { createI18n } from 'vue-i18n'
import ko from './ko.js'
import en from './en.js'

const locale = localStorage.getItem('eztag-lang') || 'ko'

export default createI18n({
  legacy: false,
  locale,
  fallbackLocale: 'ko',
  messages: { ko, en },
})
