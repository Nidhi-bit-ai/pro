import RecentDocuments from "./RecentDocuments";
import RecentSources from "./RecentSources";

export default function HomeBody() {
  return (
    <div className="home-body">

      <RecentDocuments />

      <RecentSources />

    </div>
  );
}