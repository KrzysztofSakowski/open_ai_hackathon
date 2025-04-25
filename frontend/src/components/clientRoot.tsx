"use client";

import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";

const queryClient = new QueryClient();

export function ClientRoot() {
  return (
    <QueryClientProvider client={queryClient}>
      <InnerComponent />
    </QueryClientProvider>
  );
}

export function InnerComponent() {
  const q = useQuery({
    queryKey: ["story"],
    queryFn: async () => {
      const res = await fetch("https://jsonplaceholder.typicode.com/todos/1");
      const json = res.json();
      return json;
    },
  });

  return <b>api result: {JSON.stringify(q.data)} </b>;
}
