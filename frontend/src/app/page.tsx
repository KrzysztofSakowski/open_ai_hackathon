import Image from "next/image";
import styles from "./page.module.css";
import { ClientRoot } from "@/components/clientRoot";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <ClientRoot />
      </main>
    </div>
  );
}
