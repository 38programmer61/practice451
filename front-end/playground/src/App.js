import {React, Fragment, useEffect, lazy, Suspense} from 'react'
// import logo from './logo.svg';
import './App.css';
import {Row} from 'react-bootstrap'
import { Routes, Route, Outlet, Link } from 'react-router-dom';
import Header from './PermanentComponents/Header';
import SidebarComponent from './PermanentComponents/SidebarComponent';
// import PasswordChange from './PasswordChange';
import Footer from './PermanentComponents/Footer';

const PasswordReset = lazy(() => import('./PasswordReset/PasswordReset'));
const Profile = lazy(() => import('./profile/Profile'));
const Login = lazy(() => import('./pages/Login/Login'));
const Register = lazy(() => import('./pages/Register/RegistrationForm'));
 

function App() {
  useEffect(() => {
    document.title = 'Squad Game'
    return () => {
      document.title = 'Squad Game'
    }
  }, [])

  function Framework() {
    return (
    <Fragment>
      <div style={{minHeight: '98vh'}}>
        <Row style={{maxHeight: '8vh'}}>
          <Header />
        </Row>
        <Row style={{minHeight: '92vh',  alignItems: 'stretch'}}>
          <div style={{display: 'flex', flexDirection: 'row', flexWrap: 'wrap', alignContent: 'stretch'}}>
            <SidebarComponent />
            <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', flexGrow: 5}}>
              <Outlet />
            </div>
          </div>
        </Row>
      </div>
      <Row>
        <Footer />
      </Row>
    </Fragment>)
  }

  return (
    <Routes>
      <Route path="/" element={<Framework/>}>
      
        <Route index element={<>Welcome</>} />

        <Route path="login" 
          element={
            <Suspense fallback={<>...</>}>
              <Login/>
            </Suspense>}/>

        <Route path="register" 
          element={
            <Suspense fallback={<>...</>}>
              <Register/>
            </Suspense>}/>

        <Route path="forgot-password" 
          element={
            <Suspense fallback={<>...</>}>
              <PasswordReset/>
            </Suspense>}/>

        <Route path="profile" 
          element={
            <Suspense fallback={<>...</>}>
              <Profile/>
            </Suspense>}/>

        

        {/* Using path="*"" means "match anything", so this route
              acts like a catch-all for URLs that we don't have explicit
              routes for. */}
        <Route path="*" element={<>Welcome</>} />
      </Route>
    </Routes>
  );
}

export default App;
