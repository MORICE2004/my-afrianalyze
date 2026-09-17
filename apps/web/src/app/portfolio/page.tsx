'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Check, DollarSign, Globe, Shield, Clock, Target, Droplet, AlertCircle } from 'lucide-react';
import PortfolioDashboard from '@/components/PortfolioDashboard';

const WIZARD_STEPS = [
  { id: 'capital', title: 'Capital', icon: DollarSign, question: 'How much are you looking to invest?', type: 'number', prefix: '$' },
  { id: 'market', title: 'Market', icon: Globe, question: 'Which markets interest you?', type: 'select', options: [{val: 'TZ', label: 'Tanzania (DSE)'}, {val: 'KE', label: 'Kenya (NSE)'}, {val: 'UG', label: 'Uganda (USE)'}, {val: 'EAC', label: 'Pan-EAC Region'}] },
  { id: 'risk', title: 'Risk', icon: Shield, question: 'What is your risk tolerance?', type: 'cards', options: [{val: 'Conservative', desc: 'Focus on capital preservation'}, {val: 'Moderate', desc: 'Balance of growth and stability'}, {val: 'Aggressive', desc: 'Maximize long-term growth'}] },
  { id: 'horizon', title: 'Horizon', icon: Clock, question: 'How long do you plan to invest?', type: 'slider', min: 1, max: 30, suffix: 'Years' },
  { id: 'objective', title: 'Objective', icon: Target, question: 'What is your primary goal?', type: 'cards', options: [{val: 'Income', desc: 'Regular dividend payouts'}, {val: 'Growth', desc: 'Capital appreciation'}, {val: 'Balanced', desc: 'Mix of income & growth'}] },
  { id: 'liquidity', title: 'Liquidity', icon: Droplet, question: 'How quickly might you need cash?', type: 'cards', options: [{val: 'Low', desc: 'Funds can be locked up'}, {val: 'Medium', desc: 'Need occasional access'}, {val: 'High', desc: 'Must be easily accessible'}] },
  { id: 'constraints', title: 'Constraints', icon: AlertCircle, question: 'Any specific constraints?', type: 'textarea', placeholder: 'e.g., ESG only, Shariah compliant, No mining stocks...' },
];

export default function PortfolioWizard() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completed, setCompleted] = useState(false);
  
  const [formData, setFormData] = useState({
    capital: '100000',
    market: 'TZ',
    risk: 'Moderate',
    horizon: '5',
    objective: 'Growth',
    liquidity: 'Medium',
    constraints: '',
  });

  const step = WIZARD_STEPS[currentStepIndex];
  
  const handleNext = () => {
    if (currentStepIndex < WIZARD_STEPS.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      setCompleted(true);
    }
  };

  const handleBack = () => {
    if (currentStepIndex > 0) setCurrentStepIndex(currentStepIndex - 1);
  };

  if (completed) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] p-8 font-sans">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex justify-between items-end mb-8 border-b border-gray-200 pb-4">
            <div>
              <h1 className="text-4xl font-light text-gray-900 tracking-tight">Portfolio Optimization</h1>
              <p className="text-gray-500 mt-2">Generated for {formData.risk} risk profile, {formData.horizon} year horizon.</p>
            </div>
            <button
              onClick={() => setCompleted(false)}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-black border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Adjust Parameters
            </button>
          </div>
          <PortfolioDashboard formData={formData} />
        </div>
      </div>
    );
  }

  const StepIcon = step.icon;

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 selection:bg-white selection:text-black">
      <div className="w-full max-w-3xl">
        {/* Progress bar */}
        <div className="mb-12">
          <div className="flex justify-between mb-4">
            {WIZARD_STEPS.map((s, idx) => (
              <div
                key={s.id}
                className={`flex flex-col items-center gap-2 transition-colors duration-500 ${
                  idx <= currentStepIndex ? 'text-white' : 'text-zinc-700'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${idx <= currentStepIndex ? 'bg-white' : 'bg-zinc-800'}`} />
                <span className="text-[10px] uppercase tracking-widest font-medium hidden md:block">
                  {s.title}
                </span>
              </div>
            ))}
          </div>
          <div className="w-full h-[1px] bg-zinc-800 relative">
            <motion.div 
              className="absolute left-0 top-0 h-full bg-white"
              initial={{ width: 0 }}
              animate={{ width: `${(currentStepIndex / (WIZARD_STEPS.length - 1)) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            />
          </div>
        </div>

        {/* Content Area */}
        <div className="min-h-[400px] relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStepIndex}
              initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -20, filter: 'blur(10px)' }}
              transition={{ duration: 0.4 }}
              className="absolute inset-0 flex flex-col justify-center"
            >
              <div className="flex items-center gap-4 text-zinc-400 mb-6">
                <StepIcon size={24} />
                <span className="text-sm uppercase tracking-widest font-semibold">{step.title}</span>
              </div>
              <h2 className="text-4xl md:text-5xl font-light text-white mb-12 tracking-tight">
                {step.question}
              </h2>

              <div className="w-full max-w-xl">
                {step.type === 'number' && (
                  <div className="relative">
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 text-4xl text-zinc-500 border-r border-zinc-800 pr-4">{step.prefix}</span>
                    <input
                      type="number"
                      autoFocus
                      value={formData[step.id as keyof typeof formData]}
                      onChange={(e) => setFormData({ ...formData, [step.id]: e.target.value })}
                      className="w-full bg-transparent border-b border-zinc-800 text-5xl text-white py-4 pl-16 focus:outline-none focus:border-white transition-colors"
                      placeholder="0"
                    />
                  </div>
                )}

                {step.type === 'select' && (
                  <select
                    value={formData[step.id as keyof typeof formData]}
                    onChange={(e) => setFormData({ ...formData, [step.id]: e.target.value })}
                    className="w-full bg-transparent border-b border-zinc-800 text-3xl text-white py-4 focus:outline-none focus:border-white transition-colors appearance-none cursor-pointer"
                  >
                    {step.options?.map((opt: any) => (
                      <option key={opt.val} value={opt.val} className="bg-zinc-900">
                        {opt.label || opt.val}
                      </option>
                    ))}
                  </select>
                )}

                {step.type === 'cards' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {step.options?.map((opt: any) => (
                      <button
                        key={opt.val}
                        onClick={() => setFormData({ ...formData, [step.id]: opt.val })}
                        className={`p-6 rounded-xl border text-left transition-all duration-300 ${
                          formData[step.id as keyof typeof formData] === opt.val 
                            ? 'border-white bg-white text-black' 
                            : 'border-zinc-800 bg-zinc-900 text-white hover:border-zinc-600'
                        }`}
                      >
                        <div className="font-medium text-lg mb-2">{opt.val}</div>
                        <div className={`text-sm ${formData[step.id as keyof typeof formData] === opt.val ? 'text-zinc-600' : 'text-zinc-400'}`}>
                          {opt.desc}
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {step.type === 'slider' && (
                  <div className="space-y-8">
                    <div className="text-7xl font-light text-white text-center">
                      {formData[step.id as keyof typeof formData]} <span className="text-3xl text-zinc-500">{step.suffix}</span>
                    </div>
                    <input
                      type="range"
                      min={step.min}
                      max={step.max}
                      value={formData[step.id as keyof typeof formData]}
                      onChange={(e) => setFormData({ ...formData, [step.id]: e.target.value })}
                      className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-white"
                    />
                  </div>
                )}

                {step.type === 'textarea' && (
                  <textarea
                    value={formData[step.id as keyof typeof formData]}
                    onChange={(e) => setFormData({ ...formData, [step.id]: e.target.value })}
                    rows={4}
                    placeholder={step.placeholder}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-xl text-xl text-white p-6 focus:outline-none focus:border-white transition-colors resize-none"
                  />
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="mt-12 flex justify-between items-center border-t border-zinc-900 pt-8">
          <button
            onClick={handleBack}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium tracking-wide rounded-full transition-all duration-300 ${
              currentStepIndex === 0 ? 'opacity-0 pointer-events-none' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
            }`}
          >
            <ArrowLeft size={16} /> Back
          </button>
          
          <button
            onClick={handleNext}
            className="flex items-center gap-2 px-8 py-4 bg-white text-black text-sm font-bold tracking-widest uppercase rounded-full hover:bg-zinc-200 transition-all duration-300 transform hover:scale-105"
          >
            {currentStepIndex === WIZARD_STEPS.length - 1 ? 'Analyze' : 'Continue'} 
            {currentStepIndex === WIZARD_STEPS.length - 1 ? <Check size={18} /> : <ArrowRight size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
