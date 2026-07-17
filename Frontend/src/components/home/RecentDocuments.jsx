import DocumentCard from "./DocumentCard";

const documents = [
  {
    id: 1,
    title: "Hostel Manual v2026",
    type: "PDF",
    updated: "2 days ago",
  },
  {
    id: 2,
    title: "Academic Ordinance",
    type: "PDF",
    updated: "6 days ago",
  },
  {
    id: 3,
    title: "Placement Cell Report FY26",
    type: "PDF",
    updated: "1 week ago",
  },
];


export default function RecentDocuments() {
  return (
    <>
      <div className="section-label">
        Recently Uploaded Documents
      </div>


      <div className="document-grid">

        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            {...doc}
          />
        ))}

      </div>

    </>
  );
}