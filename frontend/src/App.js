import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Navbar from './Components/Navbar/Navbar';
import Routing from './Routing';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-base-100 text-base-content">
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 py-8">
          <Routing />
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
