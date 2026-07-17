const sources = [
  "Hostel Manual v2026",
  "Academic Ordinance §4",
  "Placement Cell Report FY26",
  "Scholarship Circular 118/26",
];


export default function RecentSources(){

  return (

    <>

      <div className="section-label">
        Recently Updated Sources
      </div>


      <div className="sources-strip">

        {
          sources.map((source,index)=>(

            <div
              className="source-chip"
              key={index}
            >

              <span className="dot"></span>

              {source}

            </div>

          ))
        }

      </div>


    </>
  );
}