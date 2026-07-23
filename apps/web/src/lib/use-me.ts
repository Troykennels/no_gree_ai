"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "./api";

/** Fetch the signed-in user; redirect to /login on 401. Shared by authed pages. */
export function useMe() {
  const router = useRouter();
  const query = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false });

  useEffect(() => {
    if (query.error instanceof ApiError && query.error.status === 401) {
      router.replace("/login");
    }
  }, [query.error, router]);

  return query;
}
