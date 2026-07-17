import Sidebar from "../sidebar/Sidebar";
import { Outlet } from "react-router-dom";


export default function MainLayout(){

  return (

    <div id="app">

      <Sidebar />

      <main className="main">

        <Outlet />

      </main>


    </div>

  );

}