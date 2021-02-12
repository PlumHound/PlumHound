import { Table, Thead, Tbody, Tr, Th, Td } from "@chakra-ui/react"

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
      {values.map(row => (
        <Tr>
          {keys.map(key => {
            const value = row[key];
            if(typeof value === 'string'){
              return <Td>{value}</Td>;
            } else {
              return <Td isNumeric={true}>{value}</Td>;
            }
          })}
        </Tr>
      ))}
      </Tbody>
    </Table>
  )
}