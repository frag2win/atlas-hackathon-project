// App.jsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// This is the main component for the ATLAS application.
export default function App() {
  // State for the current view (analyst or debate)
  const [activeTab, setActiveTab] = useState('analyst');
  // State for the user's input text.
  const [topic, setTopic] = useState('');
  // State for the selected AI model.
  const [model, setModel] = useState('llama3');
  // State to hold the results from the API.
  const [results, setResults] = useState(null);
  // State to manage loading status.
  const [isLoading, setIsLoading] = useState(false);
  // State to hold any error messages.
  const [error, setError] = useState(null);

  // A ref to automatically scroll to the results.
  const resultsEndRef = useRef(null);

  // Function to handle the form submission
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (topic.trim() === '') return;

    setIsLoading(true);
    setError(null);
    setResults(null);

    const endpoint = activeTab === 'analyst' ? 'analyze_topic' : 'run_debate';
    const body = { topic, model };

    try {
      // --- THIS IS THE UPDATED LINE ---
      // It now calls your live backend server on Render.
      const response = await fetch(`https://atlas-hackathon-project.onrender.com/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  // Scrolls to the results when they appear.
  useEffect(() => {
    if (results || error) {
      resultsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [results, error]);

  // Framer Motion variants for animations.
  const sectionVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
  };

  // Helper component to render the results
  const ResultsDisplay = () => {
    if (!results) return null;

    if (activeTab === 'analyst') {
      return (
        <div className="prose prose-invert max-w-none">
          <h2 className="text-3xl font-bold border-b border-gray-700 pb-2">OSINT Analyst Report</h2>
          {results.osint_report && results.osint_report.split('\n').map((p, i) => {
            if (p.trim().match(/^\d\./)) {
              return <h3 key={i}>{p}</h3>;
            }
            return p.trim() && <p key={i}>{p}</p>;
          })}
        </div>
      );
    }

    return (
      <div className="prose prose-invert max-w-none">
        <h2 className="text-3xl font-bold border-b border-gray-700 pb-2">Debate Report</h2>
        {results.final_synthesis && (
          <div>
            <h3>Moderator Synthesis</h3>
            {results.final_synthesis.split('\n').map((p, i) => p.trim() && <p key={i}>{p}</p>)}
          </div>
        )}
        {results.debate_transcript && (
          <div>
            <h3>Debate Transcript</h3>
            {Object.entries(results.debate_transcript).map(([role, statement]) => (
              <div key={role}>
                <h4>{role.replace(/_/g, ' ').toUpperCase()}</h4>
                <p>{statement}</p>
              </div>
            ))}
          </div>
        )}
        {results.audit_report && (
          <div>
            <h3>Bias Audit Report</h3>
            {results.audit_report.split('\n').map((p, i) => p.trim() && <p key={i}>{p}</p>)}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex min-h-screen bg-gray-950 text-white font-sans">
      {/* Fixed Left Sidebar */}
      <div className="hidden md:flex w-20 flex-col items-center py-6 border-r border-gray-800 bg-gray-900/50">
        <div className="w-12 h-12 rounded-full bg-indigo-600 flex items-center justify-center mb-10 shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.5 3-9s-1.343-9-3-9m-9 9a9 9 0 019 9m-9-9a9 9 0 009-9m-9 9h12" /></svg>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col p-4 md:p-8">
        <header className="text-center mb-8">
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">ATLAS</h1>
            <p className="text-lg text-gray-400 mt-2">AI Analysis & Debate System</p>
        </header>

        <main className="bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full mx-auto">
            <div className="flex border-b border-gray-700">
                <button onClick={() => setActiveTab('analyst')} className={`flex-1 py-3 px-4 text-center font-semibold transition-colors ${activeTab === 'analyst' ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}>OSINT Analyst</button>
                <button onClick={() => setActiveTab('debate')} className={`flex-1 py-3 px-4 text-center font-semibold transition-colors ${activeTab === 'debate' ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}>Streamlined Debate</button>
            </div>

            <div className="p-6 md:p-8">
                <form onSubmit={handleFormSubmit}>
                    <p className="text-gray-400 mb-4">
                        {activeTab === 'analyst' 
                            ? "Enter a topic, and the OSINT Analyst will provide a credibility and legitimacy report."
                            : "Enter a topic for a debate between a Tech Optimist and an AI Ethicist."
                        }
                    </p>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="topic" className="block text-sm font-medium text-gray-300">Topic</label>
                            <input type="text" id="topic" value={topic} onChange={(e) => setTopic(e.target.value)} required className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" placeholder={activeTab === 'analyst' ? 'e.g., The future of quantum computing' : 'e.g., Should AI weapons be banned?'}/>
                        </div>
                        <div>
                            <label htmlFor="model" className="block text-sm font-medium text-gray-300">Select AI Model</label>
                            <select id="model" value={model} onChange={(e) => setModel(e.target.value)} className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                                <option value="llama3">Llama 3 (Default)</option>
                                <option value="mistral">Mistral</option>
                                <option value="gemma">Gemma</option>
                                <option value="phi3">Phi-3</option>
                            </select>
                        </div>
                    </div>
                    <div className="mt-6">
                        <button type="submit" disabled={isLoading} className="w-full inline-flex justify-center items-center py-3 px-6 border border-transparent shadow-sm text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-gray-800 transition-colors disabled:bg-indigo-400 disabled:cursor-not-allowed">
                            {isLoading ? 'Running...' : (activeTab === 'analyst' ? 'Analyze Topic' : 'Run Debate')}
                        </button>
                    </div>
                </form>
            </div>
        </main>
        
        <AnimatePresence>
            {(isLoading || results || error) && (
                <motion.section
                    className="mt-10 max-w-3xl w-full mx-auto"
                    variants={sectionVariants}
                    initial="hidden"
                    animate="visible"
                >
                    {isLoading && (
                        <div className="text-center py-8">
                            <div className="h-12 w-12 rounded-full border-4 border-gray-600 border-t-indigo-500 animate-spin mx-auto"></div>
                            <p className="mt-4 text-lg text-gray-400">Running analysis... This may take a moment.</p>
                        </div>
                    )}
                    {error && (
                        <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg">
                            <h3 className="font-bold">An Error Occurred</h3>
                            <p>{error}</p>
                        </div>
                    )}
                    {results && (
                        <div className="bg-gray-800 rounded-lg shadow-xl p-6 md:p-8">
                            <ResultsDisplay />
                        </div>
                    )}
                </motion.section>
            )}
        </AnimatePresence>
        <div ref={resultsEndRef} />
      </div>
    </div>
  );
}
