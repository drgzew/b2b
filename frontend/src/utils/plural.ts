// Выбор формы слова после числительного по правилам русского склонения.
// plural(1, 'работа', 'работы', 'работ')  -> 'работа'
// plural(2, 'работа', 'работы', 'работ')  -> 'работы'
// plural(5, 'работа', 'работы', 'работ')  -> 'работ'
export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}
