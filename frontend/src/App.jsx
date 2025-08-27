// App.jsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// This is the main component for the ATLAS application.
export default function App() {
  // State to hold the chat messages. Each message has a text, a sender, and an optional role.
  const [messages, setMessages] = useState([
    { text: "Hello! I am ATLAS, an AI analysis and debate system. How can I help you today?", sender: 'bot' },
  ]);

  // State for the user's input text in the message box.
  const [input, setInput] = useState('');
  // State to manage loading status.
  const [isLoading, setIsLoading] = useState(false);

  // A ref to automatically scroll to the latest message.
  const messagesEndRef = useRef(null);

  // A function to handle sending a new message.
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (input.trim() === '' || isLoading) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call the backend's intelligent agent endpoint
      const response = await fetch('http://127.0.0.1:5000/ask_agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'An API error occurred.');
      }

      const data = await response.json();
      
      // Add the bot's response to the state
      const botMessage = { 
        text: data.response, 
        sender: 'bot',
        role: data.chosen_role // Store the role for potential display
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);

    } catch (error) {
      console.error("Failed to get response:", error);
      const errorMessage = { text: `Sorry, an error occurred: ${error.message}`, sender: 'bot', role: 'error' };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Scrolls to the bottom of the message list whenever a new message is added.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Framer Motion variants for message animations.
  const messageVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
  };

  return (
    <div className="flex min-h-screen bg-gray-950 text-white font-sans">
      {/* Fixed Left Sidebar */}
      <div className="hidden md:flex w-20 flex-col items-center py-6 border-r border-gray-800 bg-gray-900/50 backdrop-filter backdrop-blur-md">
        <div className="w-12 h-12 rounded-full bg-indigo-600 flex items-center justify-center mb-10 shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.5 3-9s-1.343-9-3-9m-9 9a9 9 0 019 9m-9-9a9 9 0 009-9m-9 9h12" /></svg>
        </div>
        <div className="flex flex-col space-y-8">
          {/* Add navigation icons here if needed */}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col p-4 md:p-8 relative">
        <div className="flex-1 overflow-y-auto space-y-6 pb-24">
          <AnimatePresence>
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                variants={messageVariants}
                initial="hidden"
                animate="visible"
              >
                <div className={`max-w-xl p-4 rounded-3xl relative ${msg.sender === 'user' ? 'bg-blue-600 text-white rounded-br-none shadow-lg' : 'bg-white/5 backdrop-filter backdrop-blur-lg border border-gray-800 text-gray-200 rounded-bl-none shadow-md'}`}>
                  {msg.role && msg.sender === 'bot' && (
                    <span className="text-xs font-bold uppercase text-indigo-400 block mb-2">
                      {msg.role.replace('_', ' ')}
                    </span>
                  )}
                  {msg.text}
                </div>
              </motion.div>
            ))}
             {isLoading && (
              <motion.div
                key="loading"
                className="flex justify-start"
                variants={messageVariants}
                initial="hidden"
                animate="visible"
              >
                <div className="max-w-xl p-4 rounded-3xl bg-white/5 backdrop-filter backdrop-blur-lg border border-gray-800 text-gray-200 rounded-bl-none shadow-md">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                    <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Sticky Bottom Input Box */}
        <div className="absolute bottom-0 left-0 right-0 p-4 pt-0 md:p-8 md:pt-4 bg-gray-950">
          <form onSubmit={handleSendMessage} className="relative flex items-center space-x-2">
            <input
              type="text"
              className="flex-1 p-4 pl-12 bg-white/5 backdrop-filter backdrop-blur-lg border border-gray-800 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all duration-300 shadow-md"
              placeholder="Ask ATLAS..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="button" className="absolute left-3 text-gray-400 hover:text-indigo-500 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L21 15" /></svg>
            </button>
            <button type="submit" disabled={isLoading} className="p-3 bg-indigo-600 rounded-xl text-white shadow-lg transition-transform transform hover:scale-105 active:scale-95 disabled:bg-indigo-400 disabled:cursor-not-allowed" aria-label="Send message">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
