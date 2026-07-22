"use client";

import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, Scan, Sparkles } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Channel, Scan as ScanType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { ResultCard } from "./result-card";

const SAMPLES: { label: string; channel: Channel; text: string }[] = [
  {
    label: "Fake bank alert",
    channel: "sms",
    text: "Dear Customer, your GTBank account will be BLOCKED today. Update your BVN now via http://gtb-verify.top/login to avoid deactivation.",
  },
  {
    label: "Loan scam",
    channel: "whatsapp",
    text: "CONGRATULATIONS! You are pre-approved for an instant loan of N150,000, NO collateral. Pay a small processing fee to unlock. Apply: bit.ly/loan-ng",
  },
  {
    label: "Real credit alert",
    channel: "sms",
    text: "Access Bank: Credit Alert. Acct **4821. Amt:NGN25,000. Desc:Transfer from Chidi. Bal:NGN61,300.",
  },
];

const CHANNELS: { value: Channel; label: string }[] = [
  { value: "sms", label: "SMS" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "pos", label: "POS alert" },
  { value: "email", label: "Email" },
  { value: "other", label: "Other" },
];

export function Detector({ compact = false }: { compact?: boolean }) {
  const [message, setMessage] = useState("");
  const [channel, setChannel] = useState<Channel>("sms");

  const mutation = useMutation<ScanType, Error, void>({
    mutationFn: () => api.detect(message.trim(), channel),
  });

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 503
        ? "The fraud model is still starting up. Please try again in a moment."
        : mutation.error.message
      : mutation.error
        ? "Could not reach the SecureNaija API. Is it running?"
        : null;

  return (
    <div className="space-y-5">
      <div
        className={cn(
          "rounded-2xl border border-border bg-card p-5 shadow-sm",
          !compact && "sm:p-6",
        )}
      >
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {CHANNELS.map((c) => (
            <button
              key={c.value}
              onClick={() => setChannel(c.value)}
              aria-pressed={channel === c.value}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                channel === c.value
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {c.label}
            </button>
          ))}
        </div>

        <Textarea
          aria-label="Message to scan for fraud"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste the suspicious SMS, WhatsApp message, POS alert or loan offer here…"
          maxLength={5000}
          className={compact ? "min-h-[104px]" : "min-h-[140px]"}
        />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Try:</span>
            {SAMPLES.map((s) => (
              <button
                key={s.label}
                onClick={() => {
                  setMessage(s.text);
                  setChannel(s.channel);
                  mutation.reset();
                }}
                className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/70"
              >
                {s.label}
              </button>
            ))}
          </div>

          <Button
            onClick={() => mutation.mutate()}
            disabled={!message.trim() || mutation.isPending}
            className="min-w-[150px]"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="animate-spin" /> Analyzing…
              </>
            ) : (
              <>
                <Scan /> Analyze message
              </>
            )}
          </Button>
        </div>

        {errorText && (
          <p className="mt-3 rounded-lg bg-danger/10 px-3 py-2 text-xs font-medium text-danger">
            {errorText}
          </p>
        )}
      </div>

      <AnimatePresence mode="wait">
        {mutation.data ? (
          <ResultCard key="result" assessment={mutation.data.assessment} />
        ) : (
          !compact && (
            <motion.div
              key="hint"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center gap-2 rounded-2xl border border-dashed border-border/70 py-10 text-sm text-muted-foreground"
            >
              <Sparkles className="size-4 text-primary" />
              Your fraud analysis and explanation will appear here.
            </motion.div>
          )
        )}
      </AnimatePresence>
    </div>
  );
}
