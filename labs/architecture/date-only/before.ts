/**
 * Ponte entre o `string` ISO `YYYY-MM-DD` consumido pelo backend e datas
 * locais do navegador. Evita `toISOString()`, que pode deslocar o dia por UTC.
 */

/** `YYYY-MM-DD` local → `Date` local. Retorna `null` se vazio/inválido. */
export const parseIsoLocal = (iso: string): Date | null => {
  if (!iso) return null;
  const [year, month, day] = iso.split('-').map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day);
};

/** `Date` → `YYYY-MM-DD` no fuso local. */
export const toIsoLocal = (date: Date): string => date.toLocaleDateString('en-CA');
