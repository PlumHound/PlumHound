import { Table, Thead, Tbody, Tr, Th, Td } from "@chakra-ui/react";

export const PlumHoundTable = <T extends string>({keys, values}: {keys: T[], values: Record<T, string | number>[]}) => {
  return (
    <Table size='sm' colorScheme='gray'>
      <Thead>
        <Tr>
          {keys.map(key => (
            <Th key={key}>
              {key}
            </Th>
          ))}
        </Tr>
      </Thead>
      <Tbody>
      {values.map((row, i) => (
        <Tr key={i}>
          {keys.map(key => {
            const value = row[key];
            if(typeof value === 'string'){
              return <Td key={key}>{value}</Td>;
            } else {
              return <Td isNumeric={true} key={key}>{value}</Td>;
            }
          })}
        </Tr>
      ))}
      </Tbody>
    </Table>
  )
}