import React from 'react';
import { Route, Switch } from 'react-router-dom';
import Routes from './Routes';

function Routing() {
  return (
    <Switch>
      {Routes.map((route) => (
        <Route
          key={route.path}
          path={route.path}
          exact={route.exact}
          component={route.component}
        />
      ))}
    </Switch>
  );
}

export default Routing;
