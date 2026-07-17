import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/Dashboard/Dashboard";
import Chat from "../pages/Chat/Chat";
import Login from "../pages/Login/Login";
import Register from "../pages/Register/Register";
import Profile from "../pages/Profile/Profile";
import Documents from "../pages/Documents/Documents";
import Settings from "../pages/Settings/Settings";

import MainLayout from "../components/layout/MainLayout";


export default function AppRouter() {

  return (

    <Routes>

      <Route path="/login" element={<Login />} />

      <Route path="/register" element={<Register />} />


      <Route element={<MainLayout />}>

        <Route path="/" element={<Dashboard />} />

        <Route path="/chat/:id" element={<Chat />} />

        <Route path="/documents" element={<Documents />} />

        <Route path="/profile" element={<Profile />} />

        <Route path="/settings" element={<Settings />} />

      </Route>


    </Routes>

  );

}