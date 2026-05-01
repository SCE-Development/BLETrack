import React from 'react';
import { NavLink } from 'react-router-dom';

function Navbar() {
  const navItems = [
    { path: '/', label: 'Dashboard', exact: true },
    { path: '/devices', label: 'Devices', exact: false },
    { path: '/pairing', label: 'Pairing', exact: false },
  ];

  return (
    <nav className="navbar bg-base-200 border-b border-base-300 px-6 py-3">
      <div className="navbar-start">
        <NavLink to="/" className="flex items-center gap-3">
          <img
            src="/sce-logo.ico"
            alt="SCE Logo"
            className="w-12 h-12 object-contain"
          />
          <span className="text-xl font-bold text-white hidden sm:inline">
            BLETrack
          </span>
        </NavLink>
      </div>
      <div className="navbar-center hidden md:flex">
        <ul className="menu menu-horizontal gap-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                exact={item.exact}
                className="text-gray-300 hover:text-white px-4 py-2 rounded-lg transition-colors"
                activeClassName="!text-blue-400 !bg-base-300"
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
      <div className="navbar-end">
        <span className="text-sm text-gray-400 hidden lg:inline">
          SCE Development
        </span>
      </div>
    </nav>
  );
}

export default Navbar;
