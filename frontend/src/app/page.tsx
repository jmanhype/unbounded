import { Button } from '@mui/joy';
import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4">
          Welcome to UNBOUNDED
        </p>
        <div className="fixed right-0 top-0 flex gap-4 p-4">
          <Link href="/auth/login" passHref>
            <Button variant="outlined" color="primary">Login</Button>
          </Link>
          <Link href="/auth/register" passHref>
            <Button variant="solid" color="primary">Sign Up</Button>
          </Link>
        </div>
      </div>

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:text-left">
        <h2 className="mb-3 text-2xl font-semibold">
          Start Your Journey
        </h2>
        <p className="m-0 max-w-[30ch] text-sm opacity-50">
          Create your character and begin your adventure in an infinite world.
        </p>
      </div>
    </main>
  );
}
