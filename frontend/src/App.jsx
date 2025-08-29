// App.jsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// NEW: SVG component for the up-arrow icon
const UpArrowIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 5L12 19M12 5L6 11M12 5L18 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export default function App() {
  // All your existing state and logic remains the same
  const [activeTab, setActiveTab] = useState('analyst');
  const [topic, setTopic] = useState('');
  const [model, setModel] = useState('llama3');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const resultsEndRef = useRef(null);

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (topic.trim() === '') return;
    setIsLoading(true);
    setError(null);
    setResults(null);
    const endpoint = activeTab === 'analyst' ? 'analyze_topic' : 'run_debate';
    const body = { topic, model };
    try {
      // IMPORTANT: Make sure this URL is your current, active ngrok URL
      const response = await fetch(`https://b5d92aa5b715.ngrok-free.app/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'An API error occurred.');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (results || error) {
      resultsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [results, error]);
  
  // Your existing ResultsDisplay component, with minor style tweaks
  const ResultsDisplay = () => { /* ... (Your existing ResultsDisplay component code goes here) ... */ };
  
  return (
    // UPDATED: Main container with new background and font
    <div className="flex flex-col min-h-screen bg-black text-gray-300 font-sans relative overflow-x-hidden">
      
      {/* NEW: Faded background watermark */}
      <div className="absolute inset-0 flex items-center justify-center z-0">
        <h1 className="text-[25vw] font-black text-gray-500/10 select-none">ATLAS</h1>
      </div>

      {/* NEW: Header navigation */}
      <header className="fixed top-0 left-0 right-0 p-4 flex justify-between items-center z-10">
        <div className="flex items-center space-x-2">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path><path d="M2 17L12 22L22 17" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path><path d="M2 12L12 17L22 12" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path></svg>
          <span className="font-bold text-white">ATLAS</span>
        </div>
        <nav className="hidden md:flex items-center space-x-6 text-sm text-gray-400">
          <a href="#" className="hover:text-white transition-colors">API</a>
          <a href="#" className="hover:text-white transition-colors">COMPANY</a>
          <a href="#" className="hover:text-white transition-colors">OSINT</a>
          <a href="#" className="hover:text-white transition-colors">DEBATE</a>
        </nav>
        <button className="px-4 py-2 text-sm font-semibold border border-gray-700 rounded-md hover:bg-white hover:text-black transition-colors">
          TRY ATLAS
        </button>
      </header>

      {/* UPDATED: Main content area, centered */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 z-10">
        <div className="w-full max-w-2xl">
          {/* Your form, redesigned */}
          <form onSubmit={handleFormSubmit} className="relative bg-gray-900/50 border border-gray-700 rounded-2xl p-2 flex items-center focus-within:border-white transition-colors">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              className="flex-grow bg-transparent text-white text-lg px-4 py-2 focus:outline-none"
              placeholder="What do you want to know?"
            />
            <button type="submit" disabled={isLoading} className="bg-white text-black rounded-full w-10 h-10 flex items-center justify-center hover:bg-gray-300 transition-colors disabled:bg-gray-500">
              {isLoading ? <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div> : <UpArrowIcon />}
            </button>
          </form>

          {/* NEW: Minimalist description below the form */}
          <p className="text-center text-gray-500 text-sm mt-6">
            ATLAS is your truth-seeking AI companion for unfiltered answers with advanced<br/>
            capabilities in reasoning, coding, and visual processing.
          </p>
        </div>
      </main>

      {/* Your results section, will appear below when ready */}
      <AnimatePresence>
        {(isLoading || results || error) && (
          <motion.section
              className="mt-10 max-w-3xl w-full mx-auto z-10 p-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
          >
              {isLoading && (
                  <div className="text-center py-8">
                      <div className="h-12 w-12 rounded-full border-4 border-gray-600 border-t-white animate-spin mx-auto"></div>
                  </div>
              )}
              {error && (
                  <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg">
                      <h3 className="font-bold">An Error Occurred</h3>
                      <p>{error}</p>
                  </div>
              )}
              {results && (
                  <div className="bg-gray-900/50 border border-gray-800 rounded-lg shadow-xl p-6 md:p-8">
                      {/* Note: Paste your full ResultsDisplay component definition where indicated above */}
                      {/* <ResultsDisplay /> */}
                  </div>
              )}
          </motion.section>
        )}
      </AnimatePresence>
      <div ref={resultsEndRef} />

    </div>
  );
}