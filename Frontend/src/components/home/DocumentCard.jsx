import { FileText } from "lucide-react";


export default function DocumentCard({
  title,
  type,
  updated,
}) {

  return (

    <button className="document-card">

      <div className="document-icon">

        <FileText size={18}/>

      </div>


      <div>

        <div className="document-title">
          {title}
        </div>


        <div className="document-meta">

          {type}

          <span>
            {updated}
          </span>

        </div>

      </div>


    </button>

  );
}