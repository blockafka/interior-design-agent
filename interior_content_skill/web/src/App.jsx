import { useState } from 'react'
import NavBar from './components/NavBar'
import HeroBackground from './components/HeroBackground'
import InputView from './components/InputView'
import GeneratingView from './components/GeneratingView'
import ResultView from './components/ResultView'

export default function App() {
  const [view, setView] = useState('input')
  const [formData, setFormData] = useState(null)
  const [result, setResult] = useState(null)
  const [steps, setSteps] = useState([])
  const [elapsed, setElapsed] = useState(0)

  const handleGenerate = (data) => {
    setFormData(data)
    setSteps([])
    setResult(null)
    setView('generating')
  }

  const handleComplete = (finalResult, elapsedTime) => {
    setResult(finalResult)
    setElapsed(elapsedTime)
    setView('result')
  }

  const handleReset = () => {
    setView('input')
    setResult(null)
    setSteps([])
  }

  return (
    <div className="min-h-screen">
      <HeroBackground static={view === 'result'} />
      <NavBar />
      <main className="relative z-10 max-w-5xl mx-auto px-4 py-8">
        {view === 'input' && <InputView onGenerate={handleGenerate} />}
        {view === 'generating' && (
          <GeneratingView
            formData={formData}
            steps={steps}
            setSteps={setSteps}
            onComplete={handleComplete}
          />
        )}
        {view === 'result' && (
          <ResultView result={result} elapsed={elapsed} onReset={handleReset} />
        )}
      </main>
    </div>
  )
}
