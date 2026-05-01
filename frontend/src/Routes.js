import Dashboard from './Pages/Dashboard/Dashboard';
import Devices from './Pages/Devices/Devices';
import Pairing from './Pages/Pairing/Pairing';

const Routes = [
  {
    path: '/',
    exact: true,
    component: Dashboard,
    name: 'Dashboard',
  },
  {
    path: '/devices',
    exact: true,
    component: Devices,
    name: 'Devices',
  },
  {
    path: '/pairing',
    exact: true,
    component: Pairing,
    name: 'Pairing',
  },
];

export default Routes;
