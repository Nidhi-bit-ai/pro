export default function PageContainer({ children }) {
  return (
    <main className="flex-1 overflow-y-auto bg-[#0A0B0D]">
      {children}
    </main>
  );
}