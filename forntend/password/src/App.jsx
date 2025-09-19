
import PasswordChecker from "./components/PasswordChecker";

export default function App() {
  // theme: "light" (default), "dark", "professional"
 

  

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-3xl">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Password Strength Assistant</h1>
            <p className="text-sm text-[color:rgb(var(--muted))]">Real-time evaluation with AI suggestions (private).</p>
          </div>
          
        </header>

        <main className="card p-6">
          <PasswordChecker />
        </main>

      
      </div>
    </div>
  );
}
