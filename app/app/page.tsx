import { Hero } from '@/components/Hero';
import { Studio } from '@/components/Studio';
import { Gallery } from '@/components/Gallery';

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      <Hero />
      <Studio />
      <Gallery />
    </main>
  );
}
