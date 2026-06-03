import React from "react";
import { Text } from "react-native";
import AppCard from "./AppCard";

export default function EvidenceCard({ title, evidence }) {
  return (
    <AppCard>
      <Text style={{ fontWeight: "800" }}>{title}</Text>
      <Text>{JSON.stringify(evidence || {}, null, 2)}</Text>
    </AppCard>
  );
}
