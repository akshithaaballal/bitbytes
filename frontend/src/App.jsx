import Header from './components/Header.jsx';
import Dashboard from './pages/Dashboard.jsx';

export default function App() {
  return (
    <>
      <Header />
      <main className="page">
        <Dashboard />
      </main>
    </>
  );
}
