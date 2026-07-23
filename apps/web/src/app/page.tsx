import { redirect } from "next/navigation";

/**
 * The front page IS the auth screen. No marketing site - visitors land on
 * "Welcome back" (log in) with a link to create an account. Already-signed-in
 * users are bounced to the dashboard from the login screen.
 */
export default function HomePage() {
  redirect("/login");
}
