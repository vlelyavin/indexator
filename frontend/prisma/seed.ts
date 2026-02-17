import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  await prisma.plan.upsert({
    where: { id: "free" },
    update: {
      name: "Free",
      auditsPerMonth: 5,
      maxPages: 10,
      whiteLabel: false,
      price: 0,
    },
    create: {
      id: "free",
      name: "Free",
      auditsPerMonth: 5,
      maxPages: 10,
      whiteLabel: false,
      price: 0,
    },
  });

  await prisma.plan.upsert({
    where: { id: "pro" },
    update: {
      name: "Pro",
      auditsPerMonth: 50,
      maxPages: 100,
      whiteLabel: false,
      price: 20,
    },
    create: {
      id: "pro",
      name: "Pro",
      auditsPerMonth: 50,
      maxPages: 100,
      whiteLabel: false,
      price: 20,
    },
  });

  await prisma.plan.upsert({
    where: { id: "agency" },
    update: {
      name: "Agency",
      auditsPerMonth: 999999,
      maxPages: 500,
      whiteLabel: true,
      price: 50,
    },
    create: {
      id: "agency",
      name: "Agency",
      auditsPerMonth: 999999,
      maxPages: 500,
      whiteLabel: true,
      price: 50,
    },
  });

  console.log("Seeded 3 plans: free, pro, agency");
}

main()
  .then(() => prisma.$disconnect())
  .catch((e) => {
    console.error(e);
    prisma.$disconnect();
    process.exit(1);
  });
