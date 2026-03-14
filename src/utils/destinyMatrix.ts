export type MatrixNode = {
  key: string;
  value: number;
  x: number;
  y: number;
  size?: "lg" | "md" | "sm";
  tone?: "violet" | "blue" | "green" | "yellow" | "orange" | "red";
};

export type ChakraRow = {
  name: string;
  tone: string;
  physics: number;
  energy: number;
  emotion: number;
};

export type AgeLabel = {
  key: string;
  text: string;
};

export type DestinyMatrixVisual = {
  center: number;
  nodes: MatrixNode[];
  chakraRows: ChakraRow[];
  ageLabels: AgeLabel[];
};

function sumDigits(value: string): number {
  return value.split("").reduce((acc, char) => acc + Number(char || 0), 0);
}

function reduceArcana(value: number): number {
  let result = value;
  while (result > 22) {
    result = sumDigits(String(result));
  }
  return result <= 0 ? 22 : result;
}

export function buildDestinyMatrix(birthDate: string | null): DestinyMatrixVisual | null {
  if (!birthDate) return null;

  const [yearText, monthText, dayText] = birthDate.split("-");
  if (!yearText || !monthText || !dayText) return null;

  const day = reduceArcana(Number(dayText));
  const month = reduceArcana(Number(monthText));
  const year = reduceArcana(sumDigits(yearText));
  const bottom = reduceArcana(day + month + year);
  const center = reduceArcana(day + month + year + bottom);

  const topLeft = reduceArcana(day + month);
  const topRight = reduceArcana(month + year);
  const bottomRight = reduceArcana(year + bottom);
  const bottomLeft = reduceArcana(day + bottom);

  const topSmallLeft = reduceArcana(topLeft + center);
  const topSmallCenter = reduceArcana(month + center);
  const topSmallRight = reduceArcana(topRight + center);
  const topGreen = reduceArcana(month + bottom);

  const leftBlueOuter = reduceArcana(day + year + center);
  const leftBlueInner = reduceArcana(day + center);
  const rightOrangeInner = reduceArcana(year + center);
  const rightOrangeOuter = reduceArcana(day + year + center);

  const bottomOrangeInner = reduceArcana(center + bottom);
  const bottomOrangeMid = reduceArcana(day + year);
  const lowerWhiteLeft = reduceArcana(topLeft + bottomLeft);
  const lowerWhiteRight = reduceArcana(topRight + bottomRight);
  const innerWhiteRight = center;

  const nodes: MatrixNode[] = [
    { key: "top", value: month, x: 50, y: 8, size: "lg", tone: "violet" },
    { key: "left", value: day, x: 8, y: 50, size: "lg", tone: "violet" },
    { key: "right", value: year, x: 92, y: 50, size: "lg", tone: "red" },
    { key: "bottom", value: bottom, x: 50, y: 92, size: "lg", tone: "red" },
    { key: "center", value: center, x: 50, y: 50, size: "lg", tone: "yellow" },

    { key: "topLeft", value: topLeft, x: 18, y: 20, size: "md" },
    { key: "topRight", value: topRight, x: 82, y: 20, size: "md" },
    { key: "bottomLeft", value: bottomLeft, x: 18, y: 80, size: "md" },
    { key: "bottomRight", value: bottomRight, x: 82, y: 80, size: "md" },

    { key: "topSmallLeft", value: topSmallLeft, x: 34, y: 28, size: "sm" },
    { key: "topSmallCenter", value: topSmallCenter, x: 50, y: 22, size: "sm", tone: "blue" },
    { key: "topSmallRight", value: topSmallRight, x: 66, y: 28, size: "sm" },
    { key: "topGreen", value: topGreen, x: 50, y: 36, size: "sm", tone: "green" },

    { key: "leftBlueOuter", value: leftBlueOuter, x: 20, y: 50, size: "sm", tone: "blue" },
    { key: "leftBlueInner", value: leftBlueInner, x: 28, y: 50, size: "sm", tone: "blue" },
    { key: "rightOrangeInner", value: rightOrangeInner, x: 72, y: 50, size: "sm", tone: "orange" },
    { key: "rightOrangeOuter", value: rightOrangeOuter, x: 80, y: 50, size: "sm", tone: "orange" },

    { key: "innerWhiteRight", value: innerWhiteRight, x: 60, y: 50, size: "sm" },
    { key: "lowerWhiteLeft", value: lowerWhiteLeft, x: 34, y: 66, size: "sm" },
    { key: "lowerWhiteRight", value: lowerWhiteRight, x: 66, y: 66, size: "sm" },
    { key: "bottomOrangeMid", value: bottomOrangeMid, x: 50, y: 68, size: "sm", tone: "orange" },
    { key: "bottomOrangeInner", value: bottomOrangeInner, x: 50, y: 78, size: "sm", tone: "orange" },
  ];

  const physicsLine = [
    day,
    leftBlueOuter,
    leftBlueInner,
    day,
    center,
    rightOrangeOuter,
    year,
  ];

  const energyLine = [
    month,
    reduceArcana(topLeft + bottomRight),
    topSmallCenter,
    topGreen,
    center,
    bottomOrangeInner,
    bottom,
  ];

  const chakraRows: ChakraRow[] = [
    { name: "Сахасрара", tone: "#8a63ff", physics: physicsLine[0], energy: energyLine[0], emotion: reduceArcana(physicsLine[0] + energyLine[0]) },
    { name: "Аджна", tone: "#4a85ff", physics: physicsLine[1], energy: energyLine[1], emotion: reduceArcana(physicsLine[1] + energyLine[1]) },
    { name: "Вишудха", tone: "#2db6ff", physics: physicsLine[2], energy: energyLine[2], emotion: reduceArcana(physicsLine[2] + energyLine[2]) },
    { name: "Анахата", tone: "#7fd84a", physics: physicsLine[3], energy: energyLine[3], emotion: reduceArcana(physicsLine[3] + energyLine[3]) },
    { name: "Манипура", tone: "#ffd23c", physics: physicsLine[4], energy: energyLine[4], emotion: reduceArcana(physicsLine[4] + energyLine[4]) },
    { name: "Свадхистана", tone: "#ff9b38", physics: physicsLine[5], energy: energyLine[5], emotion: reduceArcana(physicsLine[5] + energyLine[5]) },
    { name: "Муладхара", tone: "#ff584f", physics: physicsLine[6], energy: energyLine[6], emotion: reduceArcana(physicsLine[6] + energyLine[6]) },
  ];

  const ageLabels: AgeLabel[] = [
    { key: "top", text: "20 лет" },
    { key: "right", text: "40 лет" },
    { key: "bottom", text: "60 лет" },
    { key: "left", text: "0 лет" },
  ];

  return { center, nodes, chakraRows, ageLabels };
}
