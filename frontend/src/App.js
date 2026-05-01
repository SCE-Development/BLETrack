import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Routing from './Routing';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-base-100 text-base-content">
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routing />
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
