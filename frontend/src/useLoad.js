import { useCallback, useEffect, useState } from 'react'

// โหลดข้อมูลจาก API แล้วคืน { data, error, loading, reload }
// deps เปลี่ยนเมื่อไหร่ (เช่น คำค้นหา) จะโหลดใหม่ให้เอง
export function useLoad(loader, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(loader, deps)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      setData(await load())
      setError('')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [load])

  useEffect(() => {
    // หน่วงเล็กน้อย เพื่อไม่ยิง API ทุกตัวอักษรที่พิมพ์ในช่องค้นหา
    const t = setTimeout(reload, 200)
    return () => clearTimeout(t)
  }, [reload])

  return { data, error, loading, reload }
}
